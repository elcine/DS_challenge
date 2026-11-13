"""Re-check the initial observations listed in PLAN.md against the data.

Each observation was written down after a first quick look at the raw files.
`verify_observations` runs one explicit check per observation and reports
whether the data confirms it or corrects it.

Observations that come only from the data dictionary (for example, when a field
is recorded) cannot be tested with the data and are marked "from dictionary".
"""

import pandas as pd

from src.data import INCIDENTS_PATTERN, KM_PATTERN, daily_km, find_raw_file


def _starts_with(pattern: str, prefix: bytes) -> bool:
    """True if the raw file matching `pattern` begins with the bytes `prefix`."""
    with open(find_raw_file(pattern), "rb") as file:
        return file.read(len(prefix)) == prefix


def verify_observations(
    incidents_raw: pd.DataFrame,
    km_raw: pd.DataFrame,
    incidents: pd.DataFrame,
    km: pd.DataFrame,
) -> pd.DataFrame:
    """Return one row per initial observation: check, expected, found, status."""
    rows = []

    def check(observation, how, expected, found):
        """Record one check. Confirmed when what was found equals what was expected."""
        status = "confirmed" if expected == found else "CORRECTED"
        rows.append([observation, how, str(expected), str(found), status])

    def from_dictionary(observation):
        """Record a statement taken from the data dictionary, not testable here."""
        rows.append([observation, "read in the data dictionary", "", "", "from dictionary"])

    train = incidents[incidents["incident_type"] == "T"]
    station = incidents[incidents["incident_type"] == "S"]

    # ---------------------------------------------------------------- formats
    excel_signatures = [b"\xd0\xcf\x11\xe0", b"PK"]   # old .xls and .xlsx files
    looks_like_excel = any(
        _starts_with(pattern, signature)
        for pattern in [INCIDENTS_PATTERN, KM_PATTERN]
        for signature in excel_signatures
    )
    check("Both .xls files are plain text, not Excel workbooks",
          "first bytes are an Excel signature", False, looks_like_excel)
    check("Incidents file: 45,561 rows x 26 columns",
          "shape of the raw table", (45561, 26), incidents_raw.shape)
    check("Planned-km file: 8,472 rows x 11 columns",
          "shape of the raw table", (8472, 11), km_raw.shape)
    check("Incidents file starts with a byte-order mark, km file does not",
          "first three bytes of each file", (True, False),
          (_starts_with(INCIDENTS_PATTERN, b"\xef\xbb\xbf"),
           _starts_with(KM_PATTERN, b"\xef\xbb\xbf")))
    check("Exactly one line value is corrupted (02-avr)",
          "values of `line` that are not a line", ["02-avr"],
          incidents.loc[incidents["flag_line_corrupted"], "line"].tolist())
    check("Year/month is stored as text such as janv-19",
          "share of values shaped like letters-two digits", 1.0,
          float(incidents["year_month_raw"].str.fullmatch(r"\D+-\d{2}").mean()))
    check("Times run from 02:00 to 27:41",
          "earliest start time and latest end time, as hours:minutes", "2:00 to 27:41",
          f"{incidents['start_minutes'].min() // 60}:{incidents['start_minutes'].min() % 60:02d}"
          f" to {incidents['end_minutes'].max() // 60}:{incidents['end_minutes'].max() % 60:02d}")
    check("Times mix HH:MM and HH:MM:SS formats",
          "text lengths found in the start time", [5, 8],
          sorted(incidents["start_time_raw"].str.len().unique().tolist()))
    check("Year, month, day and weekday follow the service day",
          "share of rows where weekday matches the service date", 1.0,
          float((incidents["service_date"].dt.day_of_week + 1 == incidents["weekday"]).mean()))
    check("Calendar date is one day later exactly when the start time is past 24:00",
          "rows with a later calendar date but a start time before 24:00", 0,
          int(incidents["flag_date_time_disagree"].sum()))
    check("`Incident en minutes` is in the file (it is not in the dictionary)",
          "column present in the raw file", True,
          "Incident en minutes" in incidents_raw.columns)

    # --------------------------------------------------------------- coverage
    check("Incidents cover 2019-01-01 to 2025-09-30",
          "first and last calendar date", "2019-01-01 to 2025-09-30",
          f"{incidents['calendar_date'].min().date()} to {incidents['calendar_date'].max().date()}")
    daily = daily_km(km)
    check("Planned km cover 2019-01-01 to 2023-09-30",
          "first and last date with planned km", "2019-01-01 to 2023-09-30",
          f"{daily['calendar_date'].min().date()} to {daily['calendar_date'].max().date()}")
    zero_rows = km[km["flag_zero_km"]]
    check("Zero-km duplicate rows exist only in 2019",
          "zero-km rows per year", {2019: 1460},
          zero_rows.groupby("year").size().to_dict())
    check("The zero-km duplicate is always the row with no service period",
          "zero-km rows that do have a service period", 0,
          int(zero_rows["service_period"].notna().sum()))
    check("`Tournée` is always 001 in the km file",
          "distinct values", ["001"], km["run"].unique().tolist())
    from_dictionary("Train incidents can appear more than 30 days late")

    # --------------------------------------------------- duration and type
    check("Duration is published as eight bins",
          "number of distinct bins", 8, int(incidents["duration_bin"].nunique()))
    check("29,167 train incidents and 16,394 station incidents",
          "counts by type", {"T": 29167, "S": 16394},
          incidents["incident_type"].value_counts().to_dict())
    check("Every station incident is in the lowest bin",
          "station incidents outside the lowest bin", 0,
          int((station["duration_bin_lower"] > 0).sum()))
    check("Train incidents by bin: 16450, 6304, 4377, 933, 299, 173, 107, 524",
          "counts per bin, shortest to longest",
          [16450, 6304, 4377, 933, 299, 173, 107, 524],
          train["duration_bin"].value_counts().sort_index().tolist())
    check("Some train incidents have an elapsed time outside their bin",
          "train incidents flagged as time/bin mismatch (count > 0)", True,
          bool(train["flag_time_bin_mismatch"].sum() > 0))
    from_dictionary("For train incidents the start time is the start of the customer delay")
    from_dictionary("Industry indicators ignore interruptions under 5 minutes")

    # ----------------------------------------------------------- field timing
    from_dictionary("`Symptome` is the cause attributed at the time of the incident")
    from_dictionary("Primary and secondary cause are set by analysis after the incident")
    is_mr73_stock = incidents["rolling_stock_type"] == "73"
    is_mr73_cause = incidents["secondary_cause"] == "MR-73"
    is_mpm10_stock = incidents["rolling_stock_type"] == "10"
    is_mpm10_cause = incidents["secondary_cause"] == "MPM-10"
    check("Rolling stock type mirrors the secondary cause (73 = MR-73, 10 = MPM-10)",
          "rows where the two columns disagree", 0,
          int((is_mr73_stock != is_mr73_cause).sum() + (is_mpm10_stock != is_mpm10_cause).sum()))
    check("`Ligne` has 22 distinct values",
          "distinct values", 22, int(incidents["line"].nunique()))

    # --------------------------------------------------------- missing values
    check("Causes are missing only on train incidents",
          "station incidents with a missing primary cause", 0,
          int(station["primary_cause"].isna().sum()))
    check("About 1% of incidents have no cause",
          "share with a missing primary cause, in %", 1.1,
          round(float(incidents["primary_cause"].isna().mean()) * 100, 1))
    symptom_missing_by_year = incidents.groupby("service_year")["symptom"].apply(
        lambda s: s.isna().mean()
    )
    check("Missing symptoms rise from 2022 onward",
          "highest yearly share before 2022 is below the lowest share from 2022", True,
          bool(symptom_missing_by_year.loc[:2021].max() < symptom_missing_by_year.loc[2022:].min()))
    check("`#` is the placeholder in run number, vehicle, car door and evacuation",
          "raw columns that contain `#`",
          ["Numéro de tournée", "Porte de voiture", "Véhicule", "Évacuation"],
          sorted(c for c in incidents_raw.columns if (incidents_raw[c] == "#").any()))
    check("`Code de lieu` has 230 distinct values",
          "distinct values", 230, int(incidents["location"].nunique()))

    return pd.DataFrame(rows, columns=["observation", "check", "expected", "found", "status"])
