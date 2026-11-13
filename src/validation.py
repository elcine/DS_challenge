"""Temporal validation: split train incidents by service year.

A model is always trained on earlier years and tested on a later one, never
the other way round, and never on a random mix. This mirrors how the model
would be used: trained on the past, applied to incidents that come next.
"""

import pandas as pd


def rolling_origin_folds(table: pd.DataFrame, test_years: list[int],
                         max_train_years: int | None = None) -> list[dict]:
    """Return one fold per test year.

    Each fold trains on the years before its test year and tests on that year.

    - With `max_train_years=None` the training window grows: every earlier
      year is used (an "expanding window").
    - With `max_train_years=3` only the three years just before the test year
      are used (a "sliding window"), which forgets older reporting practice.

    Each fold is a dictionary with the test year, the training years, and two
    True/False Series (`train` and `test`) aligned with `table`.
    """
    first_year = int(table["service_year"].min())
    folds = []
    for test_year in test_years:
        train_years = list(range(first_year, test_year))
        if max_train_years is not None:
            train_years = train_years[-max_train_years:]
        folds.append({
            "test_year": test_year,
            "train_years": train_years,
            "train": table["service_year"].isin(train_years),
            "test": table["service_year"] == test_year,
        })
    return folds


def describe_folds(table: pd.DataFrame, folds: list[dict], target: str) -> pd.DataFrame:
    """One row per fold: periods, rows and positives, and a check on the dates."""
    rows = []
    for fold in folds:
        train = table[fold["train"]]
        test = table[fold["test"]]
        rows.append({
            "test_year": fold["test_year"],
            "train_years": f"{fold['train_years'][0]}-{fold['train_years'][-1]}",
            "train_rows": len(train),
            "train_positives": int(train[target].sum()),
            "test_rows": len(test),
            "test_positives": int(test[target].sum()),
            "test_rate": test[target].mean(),
            # The whole training period must end before the test period starts.
            "train_ends_before_test": train["service_date"].max() < test["service_date"].min(),
            # No incident may be in both parts.
            "shared_rows": int((fold["train"] & fold["test"]).sum()),
        })
    return pd.DataFrame(rows).set_index("test_year")
