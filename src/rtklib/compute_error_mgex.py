"""Compute per-epoch horizontal/vertical SPP error for MGEX static stations
against their IGS site-log truth coordinates, and write labeled CSVs to
data/processed/.

Run as a script: `python -m src.rtklib.compute_error_mgex` from the repo root.
"""

import csv
import statistics
from pathlib import Path

from src.common.geodesy import ecef2llh, ecef_diff_to_enu, llh2ecef

ROOT = Path(__file__).resolve().parents[2]
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
TRUTH_CSV = ROOT / "data" / "external" / "mgex_station_truth_coordinates.csv"

POS_COLUMNS = [
    "time", "lat", "lon", "height", "Q", "ns",
    "sdn", "sde", "sdu", "sdne", "sdeu", "sdun", "age", "ratio",
]


def load_truth():
    truth = {}
    with open(TRUTH_CSV) as f:
        for row in csv.DictReader(f):
            x, y, z = float(row["x_ecef_m"]), float(row["y_ecef_m"]), float(row["z_ecef_m"])
            lat, lon, _ = ecef2llh(x, y, z)
            truth[row["station"]] = (x, y, z, lat, lon)
    return truth


def parse_pos_file(pos_path):
    rows = []
    with open(pos_path) as f:
        for line in f:
            if line.startswith("%") or not line.strip():
                continue
            date_str, time_str, *rest = line.split()
            rows.append([f"{date_str} {time_str}"] + rest)
    return rows


def compute_errors(station, pos_path, truth):
    truth_x, truth_y, truth_z, truth_lat, truth_lon = truth[station]
    out_rows = []
    for raw in parse_pos_file(pos_path):
        record = dict(zip(POS_COLUMNS, raw))
        lat, lon, height = float(record["lat"]), float(record["lon"]), float(record["height"])
        x, y, z = llh2ecef(lat, lon, height)
        e, n, u = ecef_diff_to_enu(x - truth_x, y - truth_y, z - truth_z, truth_lat, truth_lon)
        record["error_e"] = e
        record["error_n"] = n
        record["error_u"] = u
        record["error_h"] = (e**2 + n**2) ** 0.5
        record["error_3d"] = (e**2 + n**2 + u**2) ** 0.5
        out_rows.append(record)
    return out_rows


def main():
    truth = load_truth()
    PROCESSED.mkdir(parents=True, exist_ok=True)

    for pos_path in sorted(INTERIM.glob("*/*/spp.pos")):
        station = pos_path.parent.parent.name
        day = pos_path.parent.name
        if station not in truth:
            print(f"SKIP {station} {day}: no truth coordinates")
            continue

        rows = compute_errors(station, pos_path, truth)
        out_csv = PROCESSED / f"mgex_{station}_{day}_error.csv"
        with open(out_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        horiz = [r["error_h"] for r in rows]
        horiz_sorted = sorted(horiz)
        p95 = horiz_sorted[int(0.95 * len(horiz_sorted))]
        print(
            f"{station} {day}: n={len(rows)} "
            f"mean_h={statistics.mean(horiz):.2f}m median_h={statistics.median(horiz):.2f}m "
            f"p95_h={p95:.2f}m max_h={max(horiz):.2f}m -> {out_csv.relative_to(ROOT)}"
        )


if __name__ == "__main__":
    main()
