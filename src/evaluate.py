"""Metrics agreed in decision D4, and a bootstrap for their uncertainty.

All functions take the true outcomes `y` (True/False) and the predicted
probabilities `scores`, as NumPy arrays or pandas Series of the same length.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

# Alert budgets: the share of incidents that would be escalated.
ALERT_BUDGETS = [0.05, 0.10]

# Score bands for the calibration table (predicted probability of a major incident).
CALIBRATION_BANDS = [0.0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1.0]


def top_share(y, scores, share: float, seed: int = 0) -> tuple[float, float]:
    """Recall and precision when the `share` highest-scored incidents are flagged.

    Ties in the scores are broken at random (with a fixed seed), so that a
    baseline giving many incidents the same score gets no credit for the
    order in which the rows happen to be stored.
    """
    y = np.asarray(y, dtype=bool)
    scores = np.asarray(scores, dtype=float)
    n_flagged = int(np.ceil(share * len(y)))

    rng = np.random.default_rng(seed)
    tie_breaker = rng.random(len(y))
    # Sort by score, highest first; the random number decides between equal scores.
    order = np.lexsort((tie_breaker, -scores))
    flagged = order[:n_flagged]

    caught = y[flagged].sum()
    recall = caught / y.sum()
    precision = caught / n_flagged
    return recall, precision


def all_metrics(y, scores) -> dict:
    """Every metric of decision D4 for one set of scores."""
    y = np.asarray(y, dtype=bool)
    scores = np.asarray(scores, dtype=float)
    result = {
        "pr_auc": average_precision_score(y, scores),   # primary metric
        "roc_auc": roc_auc_score(y, scores),
        "brier": brier_score_loss(y, scores),           # lower is better
    }
    for share in ALERT_BUDGETS:
        recall, precision = top_share(y, scores, share)
        result[f"recall_top_{share:.0%}"] = float(recall)
        result[f"precision_top_{share:.0%}"] = float(precision)
    return result


def calibration_table(y, scores) -> pd.DataFrame:
    """Predicted against observed rate of major incidents, by band of predicted probability.

    For a well calibrated model the two rates are close in every band.
    """
    frame = pd.DataFrame({"y": np.asarray(y, dtype=bool), "score": np.asarray(scores, dtype=float)})
    frame["band"] = pd.cut(frame["score"], CALIBRATION_BANDS, include_lowest=True)
    table = frame.groupby("band", observed=True).agg(
        incidents=("y", "size"),
        majors=("y", "sum"),
        mean_predicted=("score", "mean"),
        observed_rate=("y", "mean"),
    )
    return table


def bootstrap_by_day(days, y, scores_by_model: dict, n_resamples: int = 1000,
                     seed: int = 0) -> pd.DataFrame:
    """Bootstrap the metrics by resampling whole service days.

    Incidents on the same day are not independent, so days are drawn with
    replacement, not single incidents. All models are evaluated on the same
    resampled days, which makes their results comparable draw by draw.

    Returns one row per resample and model, with every metric.
    """
    days = np.asarray(days)
    y = np.asarray(y, dtype=bool)
    # Row positions of each day, prepared once.
    positions = pd.Series(np.arange(len(days))).groupby(days).apply(np.array)
    day_rows = list(positions)

    rng = np.random.default_rng(seed)
    results = []
    for resample in range(n_resamples):
        drawn = rng.integers(0, len(day_rows), size=len(day_rows))
        rows = np.concatenate([day_rows[i] for i in drawn])
        if y[rows].sum() == 0:      # cannot score a sample with no major incident
            continue
        for name, scores in scores_by_model.items():
            metrics = all_metrics(y[rows], np.asarray(scores)[rows])
            metrics.update({"resample": resample, "model": name})
            results.append(metrics)
    return pd.DataFrame(results)


def interval(draws: pd.Series) -> str:
    """Format the middle 95% of bootstrap draws as text."""
    low, high = draws.quantile([0.025, 0.975])
    return f"{low:.3f} to {high:.3f}"
