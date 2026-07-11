"""Rule-based trust gates (redraft PUBLISHABLE_PROJECT_REDRAFT.md §9.1/§9.2).

Both gates use only core, single-epoch features (ns, horiz_unc, cn0_mean,
resp_abs_max) — no rolling-window features, no train/test leakage risk from
the core-vs-temporal scoping question since these features are used
identically everywhere.

trust = True unless:
  no solution, OR ns < ns_min, OR horiz_unc > horiz_unc_max,
  OR cn0_mean < cn0_min, OR resp_abs_max > resp_abs_max_max
"""

import itertools

import numpy as np
import pandas as pd

FIXED_THRESHOLDS = {
    "ns_min": 6,          # redraft's own example value
    "horiz_unc_max": 10.0,  # meters; ~ the training data's 97th-99th percentile tail
    "cn0_min": 30.0,       # dB-Hz; standard "weak signal" convention, ~5th percentile tail
    "resp_abs_max_max": 10.0,  # meters; ~90th percentile tail
}


def apply_rule_gate(df, thresholds):
    """Return a boolean Series (True = TRUST) for the given threshold dict."""
    solved = df["solution_exists"].astype(bool)
    ns = pd.to_numeric(df["ns"], errors="coerce")
    horiz_unc = pd.to_numeric(df["horiz_unc"], errors="coerce")
    cn0_mean = pd.to_numeric(df["cn0_mean"], errors="coerce")
    resp_abs_max = pd.to_numeric(df["resp_abs_max"], errors="coerce")

    trust = (
        solved
        & (ns >= thresholds["ns_min"])
        & (horiz_unc <= thresholds["horiz_unc_max"])
        & (cn0_mean >= thresholds["cn0_min"])
        & (resp_abs_max <= thresholds["resp_abs_max_max"])
    )
    return trust.fillna(False)


def _missed_unsafe_rate(predicted_trust, actual_trust):
    """Fraction of truly-unsafe epochs the gate incorrectly predicted TRUST for."""
    actual_unsafe = ~actual_trust
    if actual_unsafe.sum() == 0:
        return 0.0
    missed = predicted_trust & actual_unsafe
    return missed.sum() / actual_unsafe.sum()


def _trust_availability(predicted_trust):
    return predicted_trust.mean()


def tune_rule_gate(train_df, label_col, max_missed_unsafe_rate=0.05, n_grid=6):
    """Grid-search thresholds on TRAINING data only: maximize trust
    availability subject to missed unsafe rate <= max_missed_unsafe_rate
    (redraft §9.2's stated objective).

    Parameters
    ----------
    train_df : DataFrame
        Training fold only — never pass test-fold data here.
    label_col : str
        Name of the boolean trust-label column to tune against (e.g. "trust_5m").
    """
    ns = pd.to_numeric(train_df["ns"], errors="coerce")
    horiz_unc = pd.to_numeric(train_df["horiz_unc"], errors="coerce")
    cn0_mean = pd.to_numeric(train_df["cn0_mean"], errors="coerce")
    resp_abs_max = pd.to_numeric(train_df["resp_abs_max"], errors="coerce")
    actual_trust = train_df[label_col].astype(bool)

    # search the full practical range for each threshold — don't presume
    # whether a strict or loose value is needed, let the constrained
    # optimization decide (an earlier version of this search only tried loose
    # values and silently failed to find any combination meeting the missed-
    # unsafe-rate constraint as a result).
    ns_candidates = sorted(set(np.linspace(ns.quantile(0.0), ns.quantile(0.9), n_grid).round()))
    horiz_candidates = np.linspace(horiz_unc.quantile(0.01), horiz_unc.quantile(0.99), n_grid)
    cn0_candidates = np.linspace(cn0_mean.quantile(0.01), cn0_mean.quantile(0.99), n_grid)
    resp_candidates = np.linspace(resp_abs_max.quantile(0.01), resp_abs_max.quantile(0.99), n_grid)

    best = None
    for ns_min, horiz_max, cn0_min, resp_max in itertools.product(
        ns_candidates, horiz_candidates, cn0_candidates, resp_candidates
    ):
        thresholds = {
            "ns_min": ns_min, "horiz_unc_max": horiz_max,
            "cn0_min": cn0_min, "resp_abs_max_max": resp_max,
        }
        predicted = apply_rule_gate(train_df, thresholds)
        missed = _missed_unsafe_rate(predicted, actual_trust)
        if missed > max_missed_unsafe_rate:
            continue
        availability = _trust_availability(predicted)
        if best is None or availability > best[0]:
            best = (availability, thresholds, missed)

    if best is None:
        raise ValueError(
            f"No threshold combination on the training grid satisfies "
            f"missed_unsafe_rate <= {max_missed_unsafe_rate}"
        )
    availability, thresholds, missed = best
    return thresholds, {"train_trust_availability": availability, "train_missed_unsafe_rate": missed}
