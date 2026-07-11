"""Binary trust labels at T = 2/5/10 m (redraft PUBLISHABLE_PROJECT_REDRAFT.md §7.1).

TRUST        if solution_exists AND error_h <= T
DO_NOT_TRUST if not solution_exists OR error_h > T

This single rule serves both evaluation modes defined in
configs/project_config.yaml: full-timeline uses every row as-is; solved-only
is the same label rule restricted to solution_exists=True rows at evaluation
time (no separate label column needed).

Run as a script: `python -m src.labels.build_labels` from the repo root.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
THRESHOLDS_M = [2, 5, 10]


def add_trust_labels(df, thresholds=THRESHOLDS_M):
    """Add one boolean `trust_Tm` column per threshold (True = TRUST)."""
    df = df.copy()
    solved = df["solution_exists"].astype(bool)
    error_h = pd.to_numeric(df["error_h"], errors="coerce")
    for t in thresholds:
        df[f"trust_{t}m"] = solved & (error_h <= t)
    return df


def main():
    summary_rows = []
    for path in sorted(PROCESSED.glob("features_*.csv")):
        name = path.stem.replace("features_", "")
        df = add_trust_labels(pd.read_csv(path))
        df.to_csv(path, index=False)

        row = {"dataset": name, "n_epochs": len(df)}
        for t in THRESHOLDS_M:
            n_untrust = (~df[f"trust_{t}m"]).sum()
            row[f"pct_do_not_trust_{t}m"] = round(100 * n_untrust / len(df), 1)
        summary_rows.append(row)
        print(f"{name}: {row}")

    summary = pd.DataFrame(summary_rows)
    out_path = ROOT / "reports" / "stage4_class_balance.csv"
    summary.to_csv(out_path, index=False)
    print(f"\nClass-balance summary -> {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
