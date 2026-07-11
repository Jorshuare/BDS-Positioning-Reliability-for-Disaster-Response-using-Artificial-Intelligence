"""Hand-checkable correctness cases for the fixed rule gate — each assertion
is verifiable by reading the redraft's rule directly, not just "the code
does what the code does."
"""

import pandas as pd

from src.labels.rule_gates import FIXED_THRESHOLDS, apply_rule_gate

GOOD_ROW = {
    "solution_exists": True, "ns": 12, "horiz_unc": 3.0, "cn0_mean": 40.0, "resp_abs_max": 2.0,
}


def _row(**overrides):
    row = dict(GOOD_ROW)
    row.update(overrides)
    return pd.DataFrame([row])


def test_good_epoch_is_trusted():
    assert apply_rule_gate(_row(), FIXED_THRESHOLDS).iloc[0]


def test_no_solution_is_never_trusted():
    assert not apply_rule_gate(_row(solution_exists=False), FIXED_THRESHOLDS).iloc[0]


def test_low_satellite_count_is_never_trusted():
    assert not apply_rule_gate(_row(ns=5), FIXED_THRESHOLDS).iloc[0]  # ns_min=6
    assert apply_rule_gate(_row(ns=6), FIXED_THRESHOLDS).iloc[0]


def test_poor_geometry_is_never_trusted():
    assert not apply_rule_gate(_row(horiz_unc=10.1), FIXED_THRESHOLDS).iloc[0]  # horiz_unc_max=10
    assert apply_rule_gate(_row(horiz_unc=10.0), FIXED_THRESHOLDS).iloc[0]


def test_weak_signal_is_never_trusted():
    assert not apply_rule_gate(_row(cn0_mean=29.9), FIXED_THRESHOLDS).iloc[0]  # cn0_min=30
    assert apply_rule_gate(_row(cn0_mean=30.0), FIXED_THRESHOLDS).iloc[0]


def test_large_residual_is_never_trusted():
    assert not apply_rule_gate(_row(resp_abs_max=10.1), FIXED_THRESHOLDS).iloc[0]  # resp_abs_max_max=10
    assert apply_rule_gate(_row(resp_abs_max=10.0), FIXED_THRESHOLDS).iloc[0]
