"""Load the two raw STM files and write cleaned tables to data/processed/.

Run from the repository root:

    python -m src.data

Principles
----------
- The raw files are only ever read, never written.
- No row is dropped. Suspicious rows get a boolean `flag_...` column instead,
  so the decision to keep, correct or exclude them is made later and in the open.
- Category values stay in French, exactly as published, so they can be checked
  against the data dictionary. Only the column names are translated.
"""

from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

# The raw file names contain accented letters. macOS and Linux can encode
# those differently, so the files are found by pattern instead of exact name.
INCIDENTS_PATTERN = "Incidents*.xls"
KM_PATTERN = "Kilom*.xls"

# --------------------------------------------------------------------------
# Column names: French (as published) -> English (used in the code)
# --------------------------------------------------------------------------
INCIDENT_COLUMNS = {
    "Numero d'incident": "incident_id",
    "Type d'incident": "incident_type",          # T = train, S = station
    "Cause primaire": "primary_cause",           # set after analysis
    "Cause secondaire": "secondary_cause",       # set after analysis
    "Symptome": "symptom",                       # set at the time of the incident
    "Ligne": "line",
    "Numéro de tournée": "run_number",           # train run, "#" = none
    "Heure de l'incident": "start_time_raw",
    "Heure de reprise": "end_time_raw",
    "Incident en minutes": "duration_bin",       # not in the data dictionary
    "Véhicule": "vehicle",                       # car number, "#" = none
    "Porte de voiture": "car_door",              # door number(s), "#" = none
    "Type de matériel": "rolling_stock_type",
    "Code de lieu": "location",
    "Dommage matériel": "material_damage",       # 0/1
    "KFS": "emergency_brake",                    # 0/1, brake pulled by a customer
    "Porte": "door_involved",                    # 0/1
    "Urgence métro": "emergency_team",           # 0/1
    "CAT": "traction_power_cut",                 # 0/1
    "Évacuation": "evacuation",                  # "#" = no evacuation
    "Année civile": "service_year",
    "Année civile/mois": "year_month_raw",       # text such as "janv-19"
    "Mois calendrier": "service_month",
    "Jour du mois": "service_day",
    "Jour de la semaine": "weekday",             # 1 = Monday ... 7 = Sunday
    "Jour calendaire": "calendar_date",
}

KM_COLUMNS = {
    "Ligne": "line",
    "Période Exploitation": "service_period",    # "#" = none
    "Type de Jour": "day_type",
    "Tournée": "run",
    "Année civile": "year",
    "Année civile/mois": "year_month",
    "Année civile/semaine": "week_start",
    "Jour calendaire": "calendar_date",
    "Jour de la semaine": "weekday_name",
    "Mois calendrier": "month",
    "KM planifié": "planned_km",
}

# Duration bins in order, with the lowest and highest whole minute each covers.
# The last bin is open-ended, so it has no upper bound.
DURATION_BINS = {
    "02 min et moins": (0, 2),
    "03 à 04 min": (3, 4),
    "05 à 09 min": (5, 9),
    "10 à 14 min": (10, 14),
    "15 à 19 min": (15, 19),
    "20 à 24 min": (20, 24),
    "25 à 29 min": (25, 29),
    "30 min et plus": (30, None),
}

# Columns stored as "0" / "1" in the raw file.
BOOLEAN_COLUMNS = [
    "material_damage",
    "emergency_brake",
    "door_involved",
    "emergency_team",
    "traction_power_cut",
]

# Columns where "#" means "not applicable".
HASH_MEANS_MISSING = ["run_number", "vehicle", "car_door"]

# The four real line names. Any other value in `line` is a combination of
# lines, "Non affecté", or a corrupted value.
SINGLE_LINES = ["Ligne verte", "Ligne orange", "Ligne jaune", "Ligne bleue"]


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def find_raw_file(pattern: str) -> Path:
    """Return the single raw file that matches `pattern`."""
    matches = sorted(RAW_DIR.glob(pattern))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected exactly one file matching {pattern} in {RAW_DIR}, "
            f"found {len(matches)}."
        )
    return matches[0]


def time_to_minutes(times: pd.Series) -> pd.Series:
    """Convert "HH:MM" or "HH:MM:SS" text to minutes since the service day began.

    The STM clock keeps counting past midnight (25:30 means 1:30 am of the same
    service day), so the result can be larger than 24 * 60. Seconds are ignored.
    """
    parts = times.str.split(":", expand=True)
    hours = parts[0].astype(int)
    minutes = parts[1].astype(int)
    return hours * 60 + minutes


# --------------------------------------------------------------------------
# Incidents
# --------------------------------------------------------------------------
def load_incidents_raw() -> pd.DataFrame:
    """Read the incidents file exactly as published, every column as text."""
    return pd.read_csv(
        find_raw_file(INCIDENTS_PATTERN),
        sep=";",                # semicolon-delimited despite the .xls extension
        encoding="utf-8-sig",   # UTF-8 with a byte-order mark at the start
        dtype=str,              # no type guessing; types are set in clean_incidents
    )


def clean_incidents(raw: pd.DataFrame) -> pd.DataFrame:
    """Rename columns, set types and add flag columns. Keeps every row."""
    df = raw.rename(columns=INCIDENT_COLUMNS)

    # --- Dates ------------------------------------------------------------
    # calendar_date is the real date. The year/month/day columns follow the
    # service day, which can be one day earlier for incidents after midnight.
    df["calendar_date"] = pd.to_datetime(df["calendar_date"], format="%Y-%m-%d")
    for col in ["service_year", "service_month", "service_day", "weekday"]:
        df[col] = df[col].astype(int)
    df["service_date"] = pd.to_datetime(
        {
            "year": df["service_year"],
            "month": df["service_month"],
            "day": df["service_day"],
        }
    )

    # --- Times ------------------------------------------------------------
    # For train incidents these are the start and end of the customer delay;
    # for station incidents, the start and end of the incident itself.
    df["start_minutes"] = time_to_minutes(df["start_time_raw"])
    df["end_minutes"] = time_to_minutes(df["end_time_raw"])
    df["elapsed_minutes"] = df["end_minutes"] - df["start_minutes"]

    # --- Duration bin -----------------------------------------------------
    # Ordered category, so that comparisons such as ">= 10 min" are possible.
    df["duration_bin"] = pd.Categorical(
        df["duration_bin"], categories=list(DURATION_BINS), ordered=True
    )
    if df["duration_bin"].isna().any():
        raise ValueError("Found a duration bin that is not in DURATION_BINS.")
    # Lowest number of minutes the bin covers (0, 3, 5, 10, ...).
    df["duration_bin_lower"] = (
        df["duration_bin"].map(lambda b: DURATION_BINS[b][0]).astype(int)
    )

    # --- 0/1 indicators -> True/False ---------------------------------------
    for col in BOOLEAN_COLUMNS:
        if not df[col].isin(["0", "1"]).all():
            raise ValueError(f"Column {col} has values other than 0 and 1.")
        df[col] = df[col] == "1"

    # --- Placeholders -------------------------------------------------------
    # "#" means "not applicable": turn it into a real missing value.
    for col in HASH_MEANS_MISSING:
        df[col] = df[col].replace("#", pd.NA)
    # For evacuation, "#" means "no evacuation", which is information, not a gap.
    df["evacuation"] = df["evacuation"].replace("#", "Aucune")

    # --- Flags for suspicious rows (nothing is changed or removed) ----------
    # 1. `line` is not a recognisable line value. Known case: "02-avr", a list
    #    of lines that a spreadsheet turned into a date.
    looks_like_line = df["line"].str.startswith("Ligne") | (df["line"] == "Non affecté")
    df["flag_line_corrupted"] = ~looks_like_line

    # 2. Train incidents whose elapsed time falls outside their duration bin.
    #    One minute of tolerance, because times are recorded to the minute.
    #    Station incidents are skipped: their times describe the incident, while
    #    the bin describes the service delay, so the two are not comparable.
    bin_lower = df["duration_bin_lower"]
    bin_upper = df["duration_bin"].map(lambda b: DURATION_BINS[b][1]).astype(float)
    too_short = df["elapsed_minutes"] < bin_lower - 1
    too_long = df["elapsed_minutes"] > bin_upper + 1   # never true for the open bin
    is_train = df["incident_type"] == "T"
    df["flag_time_bin_mismatch"] = is_train & (too_short | too_long)

    # 3. End time before start time.
    df["flag_negative_elapsed"] = df["elapsed_minutes"] < 0

    # 4. The calendar date is the day after the service date, but the start
    #    time is not written past midnight (it is below 24:00). The date and the
    #    time disagree about when the incident happened.
    next_calendar_day = df["calendar_date"] > df["service_date"]
    df["flag_date_time_disagree"] = next_calendar_day & (df["start_minutes"] < 24 * 60)

    return df


# --------------------------------------------------------------------------
# Planned kilometres
# --------------------------------------------------------------------------
def load_km_raw() -> pd.DataFrame:
    """Read the planned-km file exactly as published, every column as text."""
    return pd.read_csv(
        find_raw_file(KM_PATTERN),
        sep=",",                # comma-delimited despite the .xls extension
        encoding="utf-8",
        dtype=str,
    )


def clean_km(raw: pd.DataFrame) -> pd.DataFrame:
    """Rename columns, set types and flag placeholder rows. Keeps every row."""
    df = raw.rename(columns=KM_COLUMNS)

    df["calendar_date"] = pd.to_datetime(df["calendar_date"], format="%Y-%m-%d")
    df["week_start"] = pd.to_datetime(df["week_start"], format="%Y-%m-%d")
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)

    # Decimal comma -> decimal point, then to a number.
    df["planned_km"] = df["planned_km"].str.replace(",", ".").astype(float)

    # Some line/days appear twice: one row carries the planned km and the other
    # carries zero. Which of the two has a service period varies over time
    # (sometimes the km sits on the row with period "#"), so the zero-km row is
    # identified by its km value, not by its period.
    df["flag_zero_km"] = df["planned_km"] == 0
    df["service_period"] = df["service_period"].replace("#", pd.NA)

    return df


def daily_km(km: pd.DataFrame) -> pd.DataFrame:
    """Planned km with one row per line and calendar date (zero-km rows removed)."""
    daily = km.loc[~km["flag_zero_km"], ["line", "calendar_date", "planned_km"]]
    if daily.duplicated(["line", "calendar_date"]).any():
        raise ValueError("More than one planned-km row for a line and date.")
    return daily.reset_index(drop=True)


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------
def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clean both raw files, write them to data/processed/ and return them."""
    incidents_raw = load_incidents_raw()
    km_raw = load_km_raw()

    incidents = clean_incidents(incidents_raw)
    km = clean_km(km_raw)

    # Cleaning must never add or remove rows.
    assert len(incidents) == len(incidents_raw)
    assert len(km) == len(km_raw)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    incidents.to_parquet(PROCESSED_DIR / "incidents_clean.parquet", index=False)
    km.to_parquet(PROCESSED_DIR / "planned_km_clean.parquet", index=False)
    return incidents, km


if __name__ == "__main__":
    incidents, km = build()
    print(f"incidents_clean.parquet: {len(incidents):,} rows, {incidents.shape[1]} columns")
    print(f"planned_km_clean.parquet: {len(km):,} rows, {km.shape[1]} columns")
