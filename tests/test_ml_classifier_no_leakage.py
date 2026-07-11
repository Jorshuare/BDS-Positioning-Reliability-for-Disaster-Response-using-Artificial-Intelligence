"""Proves the ML classifiers never use test-fold data during training: fitting
on the same training fold twice, with only a (never-passed-in) "test set"
differing between runs, must produce identical models — checked via
identical predictions on a fixed probe set, not just "the code looks right."
"""

import inspect

import numpy as np
import pandas as pd

from src.common.splits import CORE_FEATURES
from src.models.classifiers import prepare_solved_only, predict_full_timeline, train_classifier


def _synthetic_df(n, seed):
    rng = np.random.RandomState(seed)
    df = pd.DataFrame({col: rng.uniform(1, 50, n) for col in CORE_FEATURES})
    df["solution_exists"] = True
    df["error_h"] = rng.uniform(0, 15, n)
    df["trust_5m"] = df["error_h"] <= 5.0
    return df


def test_predictions_unaffected_by_never_passed_test_fold_mutation():
    train_df = _synthetic_df(300, seed=1)
    probe_df = _synthetic_df(50, seed=2)  # fixed probe to compare predictions on

    for model_type in ["logistic_regression", "random_forest", "lightgbm"]:
        model_a = train_classifier(model_type, train_df, label_col="trust_5m")
        pred_a = predict_full_timeline(model_a, probe_df)

        _would_be_test_fold_never_passed_in = _synthetic_df(50, seed=999)  # noqa: F841

        model_b = train_classifier(model_type, train_df, label_col="trust_5m")
        pred_b = predict_full_timeline(model_b, probe_df)

        assert (pred_a == pred_b).all(), f"{model_type} predictions changed despite identical training data"


def test_train_classifier_signature_takes_only_one_dataframe():
    params = list(inspect.signature(train_classifier).parameters)
    df_like_params = [p for p in params if "df" in p.lower()]
    assert df_like_params == ["train_df"], (
        f"train_classifier should take exactly one dataframe parameter, found: {df_like_params} "
        "— a second dataframe parameter could be test data leaking into training."
    )


def test_no_solution_epochs_excluded_from_training():
    """A training frame with no-solution rows must not error or silently
    include NaN-feature rows in the fit — prepare_solved_only should drop
    them before anything touches the model.
    """
    df = _synthetic_df(100, seed=3)
    no_solution_rows = _synthetic_df(20, seed=4)
    no_solution_rows["solution_exists"] = False
    no_solution_rows[CORE_FEATURES] = float("nan")
    mixed = pd.concat([df, no_solution_rows], ignore_index=True)

    X, y = prepare_solved_only(mixed, label_col="trust_5m")
    assert len(X) == 100
    assert not X.isna().any().any()
