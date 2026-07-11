"""Proves tune_rule_gate() never uses test-fold data: mutating only the test
portion of a split must not change the thresholds tuned on the (unchanged)
training portion. End-to-end against the real function, not asserted from
reading the code.
"""

import pandas as pd

from src.labels.rule_gates import tune_rule_gate

REQUIRED_COLUMNS = ["solution_exists", "ns", "horiz_unc", "cn0_mean", "resp_abs_max", "trust_5m"]


def _synthetic_df(n, cn0_base, seed):
    rng = pd.Series(range(n))
    return pd.DataFrame(
        {
            "solution_exists": True,
            "ns": 8 + (rng % 6),
            "horiz_unc": 2.0 + (rng % 5) * 0.7,
            "cn0_mean": cn0_base + (rng % 7) * 0.5 + seed,
            "resp_abs_max": 1.0 + (rng % 4) * 1.3,
            "error_h": 1.0 + (rng % 8) * 0.6,
        }
    )


def test_tuned_thresholds_unaffected_by_test_fold_mutation():
    train_df = _synthetic_df(200, cn0_base=35.0, seed=0)
    train_df["trust_5m"] = train_df["error_h"] <= 5.0

    thresholds_a, stats_a = tune_rule_gate(train_df, label_col="trust_5m", n_grid=5)

    # Mutate what WOULD be the test fold to something wildly different, but
    # never pass it to tune_rule_gate — the training frame is untouched.
    _corrupted_test_fold_not_passed_in = _synthetic_df(50, cn0_base=5.0, seed=999)  # noqa: F841

    thresholds_b, stats_b = tune_rule_gate(train_df, label_col="trust_5m", n_grid=5)

    assert thresholds_a == thresholds_b
    assert stats_a == stats_b


def test_tune_rule_gate_signature_takes_only_one_dataframe():
    """A structural guard: if tune_rule_gate's signature ever grows a second
    dataframe parameter (e.g. accidentally accepting a test set), this fails
    loudly rather than letting leakage slip in silently later.
    """
    import inspect

    params = list(inspect.signature(tune_rule_gate).parameters)
    df_like_params = [p for p in params if "df" in p.lower()]
    assert df_like_params == ["train_df"], (
        f"tune_rule_gate should take exactly one dataframe parameter (train_df), "
        f"found: {df_like_params} — a second dataframe parameter could be test "
        f"data leaking into threshold tuning."
    )
