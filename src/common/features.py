"""Build the per-epoch feature table: measurement-level features from RTKLIB's
`.stat` per-satellite records, plus causal (backward-looking only) rolling-
window temporal features.

All rolling windows use pandas' time-based `.rolling("Ns")` with the default
`center=False` — a window ending at the current epoch never includes a later
epoch. This is verified by `tests/test_causal_features.py`.
"""

import numpy as np
import pandas as pd

from src.common.parse_stat import parse_sat_records

ROLLING_WINDOWS_SECONDS = [3, 5, 10]


def _epoch_aggregates(sat_records):
    """Per-epoch measurement-level aggregates from a list of $SAT records."""
    rows = []
    for dt, sats in sat_records.items():
        cn0 = np.array([s["snr"] for s in sats])
        el = np.array([s["el"] for s in sats])
        az = np.array([s["az"] for s in sats])
        resp = np.array([s["resp"] for s in sats])
        rows.append(
            {
                "_stat_dt": dt,
                "n_sat_stat": len(sats),
                "cn0_mean": cn0.mean(), "cn0_min": cn0.min(), "cn0_max": cn0.max(), "cn0_std": cn0.std(),
                "el_mean": el.mean(), "el_min": el.min(), "el_max": el.max(),
                "az_std": az.std(),
                "resp_mean": resp.mean(), "resp_std": resp.std(), "resp_abs_max": np.abs(resp).max(),
            }
        )
    return pd.DataFrame(rows)


def build_feature_table(error_csv_path, stat_path, time_col):
    """Load a processed error CSV, join per-epoch .stat aggregates, add
    causal rolling-window features. Returns a time-indexed DataFrame.
    """
    df = pd.read_csv(error_csv_path)
    df["_dt"] = pd.to_datetime(df[time_col])
    df = df.sort_values("_dt").reset_index(drop=True)
    df = df.drop(columns=[time_col])

    numeric_cols = ["lat", "lon", "height", "ns", "sdn", "sde", "sdu", "error_h"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    agg = _epoch_aggregates(parse_sat_records(stat_path))
    df = df.merge(agg, left_on="_dt", right_on="_stat_dt", how="left").drop(columns=["_stat_dt"])

    df["horiz_unc"] = np.sqrt(df["sdn"] ** 2 + df["sde"] ** 2)

    df = df.set_index("_dt")

    for w in ROLLING_WINDOWS_SECONDS:
        window = f"{w}s"
        df[f"cn0_mean_roll{w}s"] = df["cn0_mean"].rolling(window, min_periods=1).mean()
        df[f"cn0_min_roll{w}s"] = df["cn0_mean"].rolling(window, min_periods=1).min()
        df[f"cn0_drop_rate_roll{w}s"] = df["cn0_mean"] - df[f"cn0_min_roll{w}s"]
        df[f"resp_mean_roll{w}s"] = df["resp_mean"].rolling(window, min_periods=1).mean()
        df[f"resp_max_roll{w}s"] = df["resp_abs_max"].rolling(window, min_periods=1).max()
        df[f"ns_min_roll{w}s"] = df["ns"].rolling(window, min_periods=1).min()
        df[f"ns_change_roll{w}s"] = df["ns"] - df[f"ns_min_roll{w}s"]
        df[f"horiz_unc_growth_roll{w}s"] = df["horiz_unc"] - df["horiz_unc"].rolling(window, min_periods=1).min()

    # position-jump between temporally-adjacent epochs only (not windowed)
    lat_rad = np.radians(df["lat"])
    lon_rad = np.radians(df["lon"])
    earth_r = 6371000.0
    dlat = lat_rad.diff()
    dlon = lon_rad.diff()
    df["position_jump_m"] = earth_r * np.sqrt(dlat**2 + (np.cos(lat_rad) * dlon) ** 2)

    # consecutive no-solution duration (seconds), causal cumulative count reset on each solution
    no_sol = ~df["solution_exists"].astype(bool)
    group = (~no_sol).cumsum()
    df["consecutive_no_solution_epochs"] = no_sol.groupby(group).cumsum()

    return df.reset_index().rename(columns={"_dt": time_col})
