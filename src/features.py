"""Build the targets and the feature sets for train incidents.

Implements two decisions recorded in PLAN.md:

- D2 (target): train incidents only; a major interruption is an incident whose
  published duration bin starts at 15 minutes or more.
- D3 (features): three nested feature sets, from fields certainly known when an
  incident starts to fields that are probably consequences of a long incident.

Typical use:

    table = build_model_table(incidents)                  # one row per train incident
    kept = fit_location_groups(table[table is training])  # learned on training rows only
    table = add_location_group(table, kept)
    X = feature_matrix(table, "headline")
    y = table["is_major"]
"""

import re

import pandas as pd

from src.data import SINGLE_LINES

# --------------------------------------------------------------------------
# Targets (decision D2): column name -> minimum duration in minutes
# --------------------------------------------------------------------------
TARGETS = {
    "is_major": 15,        # primary target
    "is_severe": 30,       # secondary view, same model scores
}

# --------------------------------------------------------------------------
# Feature sets (decision D3)
# --------------------------------------------------------------------------
# Known when the incident starts: documented as such, or inherent (time, place).
STRICT_FEATURES = [
    "symptom",            # cause attributed at the time of the incident
    "line_first",         # the line, or the first listed line for multi-line incidents
    "location_group",     # location, with rare locations grouped together
    "between_stations",   # location is a segment between two stations
    "start_hour",         # hour of the service day (24 and 25 are after midnight)
    "weekday",            # 1 = Monday ... 7 = Sunday
    "service_month",
]

# Timing not documented, but these describe the triggering event and are
# plausibly part of the first report.
FIRST_REPORT_FEATURES = [
    "has_run_number",     # a train run is attached to the incident
    "door_involved",
    "emergency_brake",
]

# Timing not documented, and mostly consequences of a long incident. Used only
# to show an upper bound: "if these indicators were known in the first minutes".
RESPONSE_FEATURES = [
    "traction_power_cut",
    "emergency_team",
    "evacuation",
    "material_damage",
    "several_lines",
]

FEATURE_SETS = {
    # Lower bound: only fields certainly known at the start.
    "strict": STRICT_FEATURES,
    # Headline model.
    "headline": STRICT_FEATURES + FIRST_REPORT_FEATURES,
    # Upper bound, not a usable model.
    "upper_bound": STRICT_FEATURES + FIRST_REPORT_FEATURES + RESPONSE_FEATURES,
}

# Columns that must never be used as features: they are the outcome, are
# derived from it, or are only known after the incident has been analysed.
NEVER_FEATURES = [
    "duration_bin", "duration_bin_lower",          # the target is built from these
    "end_time_raw", "end_minutes", "elapsed_minutes",
    "flag_time_bin_mismatch", "flag_negative_elapsed",   # computed from the end time
    "primary_cause", "secondary_cause",            # set by analysis after the incident
    "rolling_stock_type",                          # mirrors the secondary cause
    "vehicle", "car_door",                         # detail with unclear timing, left out
    "service_year",                                # would encode reporting drift
    "line", "location",                            # raw versions that can reveal a multi-line incident
] + list(TARGETS)

# --------------------------------------------------------------------------
# Labels used for unknown or grouped values
# --------------------------------------------------------------------------
UNKNOWN_LINE = "Ligne inconnue"
OTHER_LOCATION = "Autre lieu"
UNKNOWN_SYMPTOM = "Symptôme inconnu"

# Line numbers used in multi-line values such as "Ligne 1, 2, 4" (data dictionary).
LINE_BY_NUMBER = {
    "1": "Ligne verte",
    "2": "Ligne orange",
    "4": "Ligne jaune",
    "5": "Ligne bleue",
}

# A location needs at least this many training incidents to keep its own value.
MIN_LOCATION_COUNT = 100


# --------------------------------------------------------------------------
# Helpers for single values
# --------------------------------------------------------------------------
def first_line(line: str) -> str:
    """Return one line name for any value of the raw `line` column.

    A multi-line value such as "Ligne 2, 1, 4" becomes its first listed line
    ("Ligne orange"). This avoids a separate "several lines" category in the
    strict and headline sets, which would let a model learn that the incident
    spread. "Non affecté" and the corrupted value become "Ligne inconnue".
    """
    if line in SINGLE_LINES:
        return line
    match = re.match(r"Ligne (\d)", line)      # "Ligne " followed by a digit
    if match:
        return LINE_BY_NUMBER[match.group(1)]
    return UNKNOWN_LINE


def is_several_lines(line: str) -> bool:
    """True for multi-line values such as "Ligne 1, 2"."""
    return line.startswith("Ligne ") and "," in line


def clean_location(location: str) -> str:
    """Remove line lists from a location code.

    Some location codes carry the list of affected lines, which reveals a
    multi-line incident just as the `line` column does:
    - "Berri-UQAM - Ligne 1, 2, 4" becomes "Berri-UQAM";
    - a code that is only a line or a list of lines ("Ligne 1", "Ligne 1, 2")
      names no place, and goes into the "other" group.
    """
    if re.fullmatch(r"Ligne [\d, ]+", location):
        return OTHER_LOCATION
    return re.sub(r" - Ligne [\d, ]+$", "", location)


# --------------------------------------------------------------------------
# Table for modelling
# --------------------------------------------------------------------------
def build_model_table(incidents: pd.DataFrame) -> pd.DataFrame:
    """One row per train incident, with the targets and every candidate feature.

    `location_group` is not created here: it depends on which rows are used
    for training, so it is added afterwards with `add_location_group`.
    """
    train = incidents[incidents["incident_type"] == "T"]

    table = pd.DataFrame(index=train.index)
    table["incident_id"] = train["incident_id"]
    table["service_date"] = train["service_date"]
    table["service_year"] = train["service_year"]     # for splitting by time, not a feature
    table["start_minutes"] = train["start_minutes"]   # for ordering within a day
    # Kept for the sensitivity run that excludes these rows (decision D1); not a feature.
    table["flag_time_bin_mismatch"] = train["flag_time_bin_mismatch"]

    # Targets: True when the duration bin starts at or above the threshold.
    for name, minutes in TARGETS.items():
        table[name] = train["duration_bin_lower"] >= minutes

    # Strict features.
    table["symptom"] = train["symptom"].fillna(UNKNOWN_SYMPTOM)
    table["line_first"] = train["line"].map(first_line)
    table["location_clean"] = train["location"].map(clean_location)
    table["between_stations"] = train["location"].str.contains("/")   # e.g. "Crémazie/Sauvé"
    table["start_hour"] = train["start_minutes"] // 60
    table["weekday"] = train["weekday"]
    table["service_month"] = train["service_month"]

    # First-report features.
    table["has_run_number"] = train["run_number"].notna()
    table["door_involved"] = train["door_involved"]
    table["emergency_brake"] = train["emergency_brake"]

    # Response features (upper bound only).
    table["traction_power_cut"] = train["traction_power_cut"]
    table["emergency_team"] = train["emergency_team"]
    table["evacuation"] = train["evacuation"]
    table["material_damage"] = train["material_damage"]
    table["several_lines"] = train["line"].map(is_several_lines)

    return table


def fit_location_groups(training_table: pd.DataFrame,
                        min_count: int = MIN_LOCATION_COUNT) -> list[str]:
    """Return the locations frequent enough, in the training rows, to keep their own value.

    Must be called on training rows only, so that the grouping never uses
    information from the period the model is tested on.
    """
    counts = training_table["location_clean"].value_counts()
    kept = counts[counts >= min_count].index.tolist()
    # The "other" label is never a kept location, even if it is frequent.
    return [location for location in kept if location != OTHER_LOCATION]


def add_location_group(table: pd.DataFrame, kept_locations: list[str]) -> pd.DataFrame:
    """Add `location_group`: the location if it was kept, otherwise the "other" label.

    A location that never appeared in training also becomes "other".
    """
    table = table.copy()
    table["location_group"] = table["location_clean"].where(
        table["location_clean"].isin(kept_locations), OTHER_LOCATION
    )
    return table


def feature_matrix(table: pd.DataFrame, feature_set: str) -> pd.DataFrame:
    """Return the columns of the chosen feature set, after checking for leaks."""
    columns = FEATURE_SETS[feature_set]
    leaked = sorted(set(columns) & set(NEVER_FEATURES))
    if leaked:
        raise ValueError(f"Feature set '{feature_set}' contains excluded columns: {leaked}")
    return table[columns]
