"""Small helpers for the exploratory analysis in the notebook.

Nothing here chooses a target or a feature set. The functions only summarise
the cleaned tables in ways that are reused several times in the notebook.
"""

import pandas as pd

from src.data import SINGLE_LINES, daily_km

# Duration thresholds (in minutes) used to describe how long incidents last.
# They follow the lower edges of the published duration bins.
THRESHOLDS = [5, 10, 15, 30]

# One fixed colour per metro line, used in every chart. These are not the
# lines' own colours: green, orange and yellow side by side are hard to tell
# apart for colour-blind readers, so a checked palette is used and every line
# is also labelled directly on the chart.
LINE_COLORS = {
    "Ligne bleue": "#2a78d6",
    "Ligne orange": "#eb6834",
    "Ligne verte": "#1baf7a",
    "Ligne jaune": "#eda100",
}
SERIES_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]   # for other multi-series charts
GRID_COLOR = "#e1e0d9"
MUTED_COLOR = "#898781"


def train_incidents(incidents: pd.DataFrame) -> pd.DataFrame:
    """Keep train incidents only and add a simplified line column."""
    train = incidents[incidents["incident_type"] == "T"].copy()
    # The four real lines keep their name; combinations of lines, "Non affecté"
    # and the corrupted value are grouped together.
    train["line_group"] = train["line"].where(
        train["line"].isin(SINGLE_LINES), "Multiple lines or other"
    )
    return train


def duration_summary(df: pd.DataFrame, by) -> pd.DataFrame:
    """Count incidents per group and the share lasting at least 5, 10, 15 and 30 min.

    `by` is a column name or a list of column names to group on.
    """
    work = df.copy()
    share_columns = []
    for minutes in THRESHOLDS:
        column = f"share_{minutes}min_plus"
        # True when the incident's bin starts at or above the threshold.
        work[column] = work["duration_bin_lower"] >= minutes
        share_columns.append(column)

    grouped = work.groupby(by, observed=True)
    summary = grouped.size().to_frame("incidents")
    # The mean of a True/False column is the share of True values.
    summary[share_columns] = grouped[share_columns].mean()
    return summary


def incidents_per_million_km(train: pd.DataFrame, km: pd.DataFrame,
                             minutes: int = 5) -> pd.DataFrame:
    """Train incidents per million planned km, by year and line.

    Gives the rate for all train incidents and for those lasting at least
    `minutes`. Only the period covered by the km file is used, and only
    incidents assigned to a single line (a multi-line incident has no single
    km denominator).
    """
    daily = daily_km(km)
    last_km_date = daily["calendar_date"].max()

    # Planned km per year and line.
    daily["year"] = daily["calendar_date"].dt.year
    km_by_year = daily.groupby(["year", "line"])["planned_km"].sum()

    # Incidents per year and line, limited to the same period and to single lines.
    in_scope = train[
        (train["service_date"] <= last_km_date) & train["line"].isin(SINGLE_LINES)
    ].copy()
    long_column = f"incidents_{minutes}min_plus"
    in_scope["is_long"] = in_scope["duration_bin_lower"] >= minutes
    grouped = in_scope.groupby(["service_year", "line"])
    counts = pd.DataFrame(
        {
            "incidents": grouped.size(),
            long_column: grouped["is_long"].sum(),
        }
    )
    counts.index.names = ["year", "line"]

    table = counts.join(km_by_year)
    table["million_km"] = table["planned_km"] / 1e6
    table["incidents_per_million_km"] = table["incidents"] / table["million_km"]
    table[f"{long_column}_per_million_km"] = table[long_column] / table["million_km"]
    return table.drop(columns="planned_km")


def quebec_holidays(years) -> pd.DatetimeIndex:
    """Quebec statutory holidays for the given years.

    Fixed dates, plus the holidays defined by a rule (for example "first
    Monday of September"). Good Friday and Easter Monday are both included,
    since employers choose one. Days moved because a holiday falls on a
    weekend are not handled.
    """
    from dateutil.easter import easter      # date of Easter Sunday

    days = []
    for year in years:
        easter_sunday = pd.Timestamp(easter(year))
        mondays_may = pd.date_range(f"{year}-05-01", f"{year}-05-24", freq="W-MON")
        mondays_sep = pd.date_range(f"{year}-09-01", f"{year}-09-30", freq="W-MON")
        mondays_oct = pd.date_range(f"{year}-10-01", f"{year}-10-31", freq="W-MON")
        days += [
            pd.Timestamp(f"{year}-01-01"),          # New Year's Day
            easter_sunday - pd.Timedelta(days=2),   # Good Friday
            easter_sunday + pd.Timedelta(days=1),   # Easter Monday
            mondays_may[-1],                        # Journée nationale des patriotes (Monday before 25 May)
            pd.Timestamp(f"{year}-06-24"),          # Fête nationale
            pd.Timestamp(f"{year}-07-01"),          # Canada Day
            mondays_sep[0],                         # Labour Day (first Monday of September)
            mondays_oct[1],                         # Thanksgiving (second Monday of October)
            pd.Timestamp(f"{year}-12-25"),          # Christmas Day
        ]
    return pd.DatetimeIndex(days)


def style_axes(ax, title: str, ylabel: str = "") -> None:
    """Apply the same quiet look to every chart: light grid, no box."""
    ax.set_title(title, loc="left", fontsize=11)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(MUTED_COLOR)
    ax.tick_params(colors=MUTED_COLOR, length=0)
