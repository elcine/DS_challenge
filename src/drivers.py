"""Driver analysis: where do major incidents come from, looking back?

This is description of past incidents, not prediction. It may therefore use
fields that are only known after an incident (the primary and secondary
cause), which the predictive model is not allowed to use.

Results are associations. A cause with many major incidents is where the
major incidents were recorded, not proof of what made them long.
"""

import pandas as pd

from src.features import clean_location

MAJOR_MINUTES = 15          # same definition of "major" as the model target (decision D2)
TOP_BIN_LOWER_EDGE = 30     # lower edge of the open-ended bin "30 min et plus"

# Fixed lists of station names, as written in the data. Not taken from the
# line field. Berri-UQAM and Snowdon are also terminals (yellow and blue
# lines); they are counted as interchanges.
INTERCHANGE_STATIONS = ["Berri-UQAM", "Lionel-Groulx", "Snowdon", "Jean-Talon"]
TERMINAL_STATIONS = ["Angrignon", "Honorée-Beaugrand", "Côte-Vertu", "Montmorency",
                     "St-Michel", "Longueuil"]


def add_driver_columns(train: pd.DataFrame) -> pd.DataFrame:
    """Add `is_major`, `estimated_minutes`, `location_clean` and `station_type`."""
    train = train.copy()
    train["is_major"] = train["duration_bin_lower"] >= MAJOR_MINUTES

    # Estimated delay minutes. The data only gives a duration bin:
    # - closed bins count for their lower edge (a "15 à 19 min" incident counts 15);
    # - the open bin "30 min et plus" counts for the median elapsed time (end
    #   minus start) of the incidents in that bin, instead of 30.
    in_top_bin = train["duration_bin_lower"] == TOP_BIN_LOWER_EDGE
    top_bin_minutes = train.loc[in_top_bin, "elapsed_minutes"].median()
    train["estimated_minutes"] = train["duration_bin_lower"].where(~in_top_bin, top_bin_minutes)

    # Location without line lists, then a simple station type.
    train["location_clean"] = train["location"].map(clean_location)
    train["station_type"] = "Other location"
    train.loc[train["location_clean"].isin(TERMINAL_STATIONS), "station_type"] = "Terminal station"
    train.loc[train["location_clean"].isin(INTERCHANGE_STATIONS), "station_type"] = "Interchange station"
    return train


def driver_table(train: pd.DataFrame, by) -> pd.DataFrame:
    """Break major incidents down by `by` (a column name or a list of names).

    Columns:
    - incidents:              all train incidents in the group
    - majors:                 incidents of 15 minutes or more
    - share_of_majors:        the group's share of all major incidents
    - major_rate:             share of the group's incidents that are major
    - major_minutes:          estimated delay minutes of its major incidents
    - share_of_major_minutes: the group's share of all those minutes

    Sorted by number of major incidents, then by minutes.
    """
    majors_only = train[train["is_major"]]
    grouped = train.groupby(by, observed=True, dropna=False)

    table = pd.DataFrame({
        "incidents": grouped.size(),
        "majors": grouped["is_major"].sum(),
    })
    table["share_of_majors"] = table["majors"] / len(majors_only)
    table["major_rate"] = table["majors"] / table["incidents"]
    minutes = majors_only.groupby(by, observed=True, dropna=False)["estimated_minutes"].sum()
    table["major_minutes"] = minutes.reindex(table.index).fillna(0)
    table["share_of_major_minutes"] = table["major_minutes"] / majors_only["estimated_minutes"].sum()

    return table.sort_values(["majors", "major_minutes"], ascending=False)
