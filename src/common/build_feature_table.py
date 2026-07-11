"""Drive feature-table construction for every MGEX station-day and UrbanNav
sequence, writing data/processed/features_<name>.csv.

Run as a script: `python -m src.common.build_feature_table` from the repo root.
"""

from pathlib import Path

from src.common.features import build_feature_table

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
INTERIM = ROOT / "data" / "interim"


def main():
    for error_csv in sorted(PROCESSED.glob("mgex_*_error.csv")):
        name = error_csv.stem.replace("_error", "")
        _, station, day = name.split("_")
        stat_path = INTERIM / station / day / "spp.pos.stat"
        df = build_feature_table(error_csv, stat_path, time_col="time")
        out_path = PROCESSED / f"features_{name}.csv"
        df.to_csv(out_path, index=False)
        print(f"{name}: {len(df)} rows, {len(df.columns)} columns -> {out_path.relative_to(ROOT)}")

    for error_csv in sorted(PROCESSED.glob("urbannav_*_error.csv")):
        name = error_csv.stem.replace("_error", "")
        sequence = name.replace("urbannav_", "")
        stat_path = INTERIM / "urbannav" / sequence / "spp.pos.stat"
        df = build_feature_table(error_csv, stat_path, time_col="gps_dt")
        out_path = PROCESSED / f"features_{name}.csv"
        df.to_csv(out_path, index=False)
        print(f"{name}: {len(df)} rows, {len(df.columns)} columns -> {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
