"""The consolidated results table: fixed rule gate, tuned rule gate, logistic
regression, random forest, and LightGBM, across all 6 validation splits
(src/common/splits.py), all 3 thresholds, both evaluation modes. Every rule-
gate and ML-classifier threshold/parameter is fit on the training fold only —
see tests/test_rule_gate_no_leakage.py and tests/test_ml_classifier_no_leakage.py.

Supersedes src/labels/evaluate_rule_gates.py (Stage 4's LOSO-only demo) with
the full experiment suite feeding Stage 6/7 directly.

Run as a script: `python -m src.models.run_all_experiments` from the repo root.
"""

from pathlib import Path

import pandas as pd

from src.common.splits import all_splits, load_datasets
from src.labels.rule_gates import FIXED_THRESHOLDS, apply_rule_gate, tune_rule_gate
from src.models.classifiers import predict_full_timeline, train_classifier
from src.models.metrics import compute_metrics

ROOT = Path(__file__).resolve().parents[2]
THRESHOLDS_M = [2, 5, 10]
ML_MODEL_TYPES = ["logistic_regression", "random_forest", "lightgbm"]
SEED = 42  # src.models.classifiers.SEED — recorded here too for the results log


def _evaluate(predicted, df, label_col, mode):
    if mode == "solved_only":
        mask = df["solution_exists"].astype(bool)
        return compute_metrics(predicted[mask], df.loc[mask, label_col])
    return compute_metrics(predicted, df[label_col])


def main():
    rows = []
    for split_name, train_names, test_names, drop_temporal in all_splits():
        train_df = load_datasets(train_names, drop_temporal)
        test_df = load_datasets(test_names, drop_temporal)

        for t in THRESHOLDS_M:
            label_col = f"trust_{t}m"

            methods = {
                "fixed_rule_gate": apply_rule_gate(test_df, FIXED_THRESHOLDS),
            }

            tuned_thresholds, _ = tune_rule_gate(train_df, label_col=label_col, n_grid=10)
            methods["tuned_rule_gate"] = apply_rule_gate(test_df, tuned_thresholds)

            for model_type in ML_MODEL_TYPES:
                model = train_classifier(model_type, train_df, label_col=label_col)
                methods[model_type] = predict_full_timeline(model, test_df)

            for method_name, predicted in methods.items():
                for mode in ["full_timeline", "solved_only"]:
                    metrics = _evaluate(predicted, test_df, label_col, mode)
                    rows.append(
                        {
                            "split": split_name, "threshold_m": t, "method": method_name,
                            "evaluation_mode": mode, "seed": SEED, **metrics,
                        }
                    )
            print(f"done: split={split_name} threshold={t}m")

    results = pd.DataFrame(rows)
    out_path = ROOT / "results" / "tables" / "stage5_all_results.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(out_path, index=False)
    print(f"\n{len(results)} rows -> {out_path.relative_to(ROOT)}")
    return results


if __name__ == "__main__":
    main()
