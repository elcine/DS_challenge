"""Baselines and models (decision D6), each trained on one period and scored on a later one.

Everything goes through `fit_and_score`, which takes training rows and test
rows and returns one predicted probability per test row. Anything that is
learned (location groups, symptom rates, model weights) is learned from the
training rows only.

Models
------
- "constant"  baseline: every incident gets the training base rate.
- "symptom"   baseline: every incident gets the training rate of its symptom.
- "logistic"  regularised logistic regression on one-hot encoded features.
- "boosting"  gradient boosting (scikit-learn HistGradientBoostingClassifier).
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

from src import features

# Features treated as categories. The time fields are included because their
# relation to the target is not a straight line (risk rises through the day
# and drops after midnight). The remaining features are True/False.
CATEGORICAL = ["symptom", "line_first", "location_group", "evacuation",
               "start_hour", "weekday", "service_month"]

# Regularisation strengths tried for the logistic regression. In scikit-learn
# a smaller C means stronger regularisation.
LOGISTIC_C_VALUES = [0.1, 1.0, 10.0]

# Fixed, conservative settings for gradient boosting: small trees, a slow
# learning rate and leaves that must hold many incidents. Not tuned, because
# a few hundred positives per training fold would mostly reward noise.
BOOSTING_SETTINGS = {
    "learning_rate": 0.05,
    "max_iter": 200,            # number of trees
    "max_leaf_nodes": 8,
    "min_samples_leaf": 50,
    "l2_regularization": 1.0,
    "early_stopping": False,
    "random_state": 0,
}


def make_logistic(columns: list[str], C: float) -> Pipeline:
    """Logistic regression with L2 regularisation and no class weights.

    Categories are one-hot encoded: one 0/1 column per value. A value never
    seen in training gets all zeros. Class weights are left out on purpose:
    they would inflate the predicted probabilities.
    """
    categorical = [c for c in columns if c in CATEGORICAL]
    encode = ColumnTransformer(
        [("onehot", OneHotEncoder(handle_unknown="ignore"), categorical)],
        remainder="passthrough",            # True/False columns are used as they are
        verbose_feature_names_out=False,    # keep readable names for the coefficients
    )
    classifier = LogisticRegression(C=C, max_iter=2000)   # L2 penalty is the default
    return Pipeline([("encode", encode), ("classifier", classifier)])


def make_boosting(columns: list[str]) -> Pipeline:
    """Gradient boosting with fixed settings and no class weights.

    Text categories are turned into integer codes, and the model is told which
    columns are categories. A value never seen in training gets the code -1,
    which the model treats as missing.
    """
    text_columns = [c for c in columns if c in CATEGORICAL
                    and c not in ("start_hour", "weekday", "service_month")]
    encode = ColumnTransformer(
        [("codes", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
          text_columns)],
        remainder="passthrough",
        verbose_feature_names_out=False,
    )
    # After encoding, the text columns come first; flag them as categorical.
    is_category = [True] * len(text_columns) + [False] * (len(columns) - len(text_columns))
    classifier = HistGradientBoostingClassifier(categorical_features=is_category,
                                                **BOOSTING_SETTINGS)
    return Pipeline([("encode", encode), ("classifier", classifier)])


def fit_and_score(model_name: str, train: pd.DataFrame, test: pd.DataFrame,
                  feature_set: str = "headline", target: str = "is_major",
                  C: float = 1.0, return_model: bool = False):
    """Train on `train`, return the predicted probability for each row of `test`.

    `train` and `test` are rows of the table from `features.build_model_table`.
    With `return_model=True` the fitted pipeline is returned as well (models only).
    """
    y_train = train[target]

    if model_name == "constant":
        return np.full(len(test), y_train.mean())

    if model_name == "symptom":
        rate_by_symptom = y_train.groupby(train["symptom"]).mean()
        # A symptom never seen in training falls back to the overall rate.
        return test["symptom"].map(rate_by_symptom).fillna(y_train.mean()).to_numpy()

    # Location groups are learned from the training rows, then applied to both.
    kept_locations = features.fit_location_groups(train)
    X_train = features.feature_matrix(features.add_location_group(train, kept_locations), feature_set)
    X_test = features.feature_matrix(features.add_location_group(test, kept_locations), feature_set)

    columns = list(X_train.columns)
    if model_name == "logistic":
        model = make_logistic(columns, C)
    elif model_name == "boosting":
        model = make_boosting(columns)
    else:
        raise ValueError(f"Unknown model: {model_name}")

    model.fit(X_train, y_train)
    scores = model.predict_proba(X_test)[:, 1]     # probability of the positive class
    return (scores, model) if return_model else scores


def score_folds(model_name: str, table: pd.DataFrame, folds: list[dict], **options) -> pd.DataFrame:
    """Score every fold's test year with a model trained on that fold's training years.

    Returns the test rows of all folds, with two extra columns: `score` (the
    predicted probability) and `test_year`.
    """
    pieces = []
    for fold in folds:
        test = table[fold["test"]].copy()
        test["score"] = fit_and_score(model_name, table[fold["train"]], test, **options)
        test["test_year"] = fold["test_year"]
        pieces.append(test)
    return pd.concat(pieces)


def logistic_coefficients(model: Pipeline) -> pd.DataFrame:
    """Coefficients of a fitted logistic regression, as a readable table.

    The odds ratio is exp(coefficient): 2 means the odds of a major incident
    double when the feature is present, 0.5 means they halve, other features
    being equal. These are associations, not causes.
    """
    names = model.named_steps["encode"].get_feature_names_out()
    coefficients = model.named_steps["classifier"].coef_[0]
    table = pd.DataFrame({"feature": names, "coefficient": coefficients})
    table["odds_ratio"] = np.exp(table["coefficient"])
    return table.sort_values("coefficient", ascending=False).reset_index(drop=True)
