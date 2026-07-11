"""ML trust classifiers (redraft PUBLISHABLE_PROJECT_REDRAFT.md §9.3-9.5):
logistic regression, random forest, LightGBM — all class-weighted (not
SMOTE, per CLAUDE.md §4), fixed seeds.

No-solution epochs have every core feature as NaN (verified in PROGRESS.md
Stage 5) — there is nothing for a feature-based model to learn from on those
rows. So, matching the rule gates' own "no_gnss_solution -> trust=False"
short-circuit (redraft §9.1), these classifiers are trained and make their
feature-based prediction only on solved epochs; `predict_full_timeline`
composes that prediction with the trivial no-solution rule for full-timeline
evaluation.
"""

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from lightgbm import LGBMClassifier

from src.common.splits import CORE_FEATURES

SEED = 42


def _model(model_type):
    if model_type == "logistic_regression":
        # scaled inside a Pipeline so the scaler is fit on the training fold
        # only (Pipeline.fit computes scaling params from X_train and reuses
        # them at predict time — no test-fold statistics leak in). Also fixes
        # the lbfgs non-convergence warning caused by unscaled, differently-
        # ranged features (ns ~10s, cn0 ~10-50, el ~0-90, etc.)
        return make_pipeline(
            StandardScaler(),
            LogisticRegression(class_weight="balanced", max_iter=1000, random_state=SEED),
        )
    if model_type == "random_forest":
        return RandomForestClassifier(class_weight="balanced", n_estimators=300, random_state=SEED)
    if model_type == "lightgbm":
        return LGBMClassifier(class_weight="balanced", random_state=SEED, verbosity=-1)
    raise ValueError(f"unknown model_type: {model_type}")


def prepare_solved_only(df, label_col, feature_cols=CORE_FEATURES):
    """Restrict to solution_exists=True rows and assert features are complete
    there (a pinned invariant, per CLAUDE.md's reproducibility standard — if
    this ever fails it means an upstream data change needs investigating, not
    silent imputation).
    """
    solved = df[df["solution_exists"].astype(bool)].copy()
    n_missing = solved[feature_cols].isna().sum().sum()
    if n_missing:
        raise ValueError(
            f"{n_missing} NaN values found among core features on solved epochs — "
            "expected zero (Stage 3 verified NaN iff not solution_exists); "
            "investigate before training on this data."
        )
    return solved[feature_cols], solved[label_col].astype(bool)


def train_classifier(model_type, train_df, label_col, feature_cols=CORE_FEATURES):
    """Fit on the training fold's solved epochs only. Never pass test-fold
    data here — see tests/test_ml_classifier_no_leakage.py.
    """
    X_train, y_train = prepare_solved_only(train_df, label_col, feature_cols)
    model = _model(model_type)
    model.fit(X_train, y_train)
    return model


def predict_full_timeline(model, df, feature_cols=CORE_FEATURES):
    """Predicted trust for every row: False where no solution exists
    (trivial rule, matches the rule gates), model's prediction otherwise.
    """
    solved_mask = df["solution_exists"].astype(bool)
    predicted = solved_mask.copy()
    predicted[:] = False
    if solved_mask.any():
        X = df.loc[solved_mask, feature_cols]
        predicted.loc[solved_mask] = model.predict(X)
    return predicted
