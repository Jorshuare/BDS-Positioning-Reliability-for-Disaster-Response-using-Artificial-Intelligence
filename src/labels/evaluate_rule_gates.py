"""Evaluate the fixed and tuned rule gates across the MGEX leave-one-station-out
splits, at all 3 thresholds, in both evaluation modes (full-timeline and
solved-only — configs/project_config.yaml `evaluation:`). Tuned-gate
thresholds are always fit on the training fold only (src/labels/rule_gates.py
tune_rule_gate), never on the held-out test fold.

This is a demonstration/verification of the rule-gate mechanism for Stage 4,
not the full Stage 5/6 experiment suite (which also runs the ML classifiers
and the cross-domain/mixed-domain splits into the same results table).

Run as a script: `python -m src.labels.evaluate_rule_gates` from the repo root.
"""

from pathlib import Path

import pandas as pd

from src.common.splits import loso_mgex_splits, load_datasets
from src.labels.rule_gates import FIXED_THRESHOLDS, apply_rule_gate, tune_rule_gate
from src.models.metrics import compute_metrics

ROOT = Path(__file__).resolve().parents[2]
THRESHOLDS_M = [2, 5, 10]


def _evaluate(predicted, actual_col, df, mode):
    if mode == "solved_only":
        mask = df["solution_exists"].astype(bool)
        predicted, actual = predicted[mask], df.loc[mask, actual_col]
    else:
        actual = df[actual_col]
    return compute_metrics(predicted, actual.astype(bool))


def main():
    rows = []
    for split_name, train_names, test_names, drop_temporal in loso_mgex_splits():
        train_df = load_datasets(train_names, drop_temporal)
        test_df = load_datasets(test_names, drop_temporal)

        for t in THRESHOLDS_M:
            label_col = f"trust_{t}m"

            fixed_pred = apply_rule_gate(test_df, FIXED_THRESHOLDS)
            tuned_thresholds, train_stats = tune_rule_gate(train_df, label_col=label_col, n_grid=10)
            tuned_pred = apply_rule_gate(test_df, tuned_thresholds)

            for gate_name, pred in [("fixed_rule_gate", fixed_pred), ("tuned_rule_gate", tuned_pred)]:
                for mode in ["full_timeline", "solved_only"]:
                    metrics = _evaluate(pred, label_col, test_df, mode)
                    rows.append(
                        {
                            "split": split_name, "threshold_m": t, "method": gate_name,
                            "evaluation_mode": mode, **metrics,
                        }
                    )

    results = pd.DataFrame(rows)
    out_path = ROOT / "results" / "tables" / "stage4_rule_gate_results.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(out_path, index=False)
    print(results.to_string(index=False))
    print(f"\n-> {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
