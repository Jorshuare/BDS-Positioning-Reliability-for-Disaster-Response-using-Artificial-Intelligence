"""Proves the rolling-window features are causal: mutating a *later* epoch's
raw diagnostics must not change a feature value already computed at an
*earlier* epoch. This is an end-to-end test against the real
build_feature_table function, not just an assumption about pandas defaults.
"""

import csv
from datetime import datetime, timedelta

from src.common.features import build_feature_table

GPS_EPOCH = datetime(1980, 1, 6)
WEEK = 2200
ERROR_COLUMNS = [
    "station", "day", "time", "solution_exists", "lat", "lon", "height", "Q", "ns",
    "sdn", "sde", "sdu", "sdne", "sdeu", "sdun", "age", "ratio",
    "error_e", "error_n", "error_u", "error_h", "error_3d",
]


def _epoch_time(tow):
    return (GPS_EPOCH + timedelta(weeks=WEEK, seconds=tow)).isoformat()


def _write_dataset(tmp_path, cn0_at_t3_t4):
    """5 epochs 1s apart. cn0 at t0..t2 is always 50; cn0 at t3/t4 is a
    parameter, so the test can flip it between two values and check whether
    a rolling feature computed at t2 (which never includes t3/t4) changes.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    tows = [100000, 100001, 100002, 100003, 100004]
    cn0_values = [50.0, 50.0, 50.0, cn0_at_t3_t4, cn0_at_t3_t4]

    error_csv = tmp_path / "error.csv"
    with open(error_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ERROR_COLUMNS)
        writer.writeheader()
        for i, tow in enumerate(tows):
            writer.writerow(
                {
                    "station": "TEST", "day": "1", "time": _epoch_time(tow),
                    "solution_exists": True, "lat": 30.0 + i * 1e-7, "lon": 114.0, "height": 50.0,
                    "Q": 5, "ns": 10, "sdn": 2.0, "sde": 2.0, "sdu": 4.0,
                    "sdne": 0, "sdeu": 0, "sdun": 0, "age": 0, "ratio": 0,
                    "error_e": 1.0, "error_n": 1.0, "error_u": 1.0, "error_h": 1.4, "error_3d": 1.7,
                }
            )

    stat_path = tmp_path / "spp.pos.stat"
    with open(stat_path, "w") as f:
        for tow, cn0 in zip(tows, cn0_values):
            f.write(f"$SAT,{WEEK},{tow}.000,C01,1,100.0,45.0,-1.0,0.0,0,{cn0},0,0,0,0,0,0\n")

    return error_csv, stat_path


def test_rolling_feature_at_earlier_epoch_is_unaffected_by_later_epoch_change(tmp_path):
    csv_a, stat_a = _write_dataset(tmp_path / "a", cn0_at_t3_t4=50.0)
    df_a = build_feature_table(csv_a, stat_a, time_col="time")

    csv_b, stat_b = _write_dataset(tmp_path / "b", cn0_at_t3_t4=5.0)  # drastically different future value
    df_b = build_feature_table(csv_b, stat_b, time_col="time")

    for col in ["cn0_mean_roll3s", "cn0_min_roll3s", "cn0_drop_rate_roll3s"]:
        value_a = df_a.loc[2, col]  # epoch t2 — its 3s window is [t(-1)..t2], never reaches t3/t4
        value_b = df_b.loc[2, col]
        assert value_a == value_b, (
            f"{col} at epoch t2 changed ({value_a} -> {value_b}) when only a "
            "LATER epoch's raw data changed — rolling feature is not causal."
        )

    # sanity: the later epoch's own feature DOES reflect the changed value,
    # proving the test setup actually exercises the changed data at all.
    assert df_a.loc[4, "cn0_mean_roll3s"] != df_b.loc[4, "cn0_mean_roll3s"]
