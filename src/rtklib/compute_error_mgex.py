"""Reconstruct the full per-epoch timeline for each MGEX station-day from the
raw observation file, join RTKLIB's BDS-only SPP solution onto it, and compute
horizontal/vertical error against IGS site-log truth coordinates.

Epochs where RTKLIB attempted a fix but failed (Q=0, dropped from `.pos`) are
kept as explicit no-solution rows rather than silently disappearing — the same
treatment used for the UrbanNav sequences, since a trust monitor needs to see
these failures too, even at "clean" static stations.

Run as a script: `python -m src.rtklib.compute_error_mgex` from the repo root.
"""

import csv
import statistics
from datetime import datetime
from pathlib import Path

from src.common.geodesy import ecef2llh, ecef_diff_to_enu, llh2ecef

ROOT = Path(__file__).resolve().parents[2]
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
TRUTH_CSV = ROOT / "data" / "external" / "mgex_station_truth_coordinates.csv"

POS_COLUMNS = [
    "lat", "lon", "height", "Q", "ns",
    "sdn", "sde", "sdu", "sdne", "sdeu", "sdun", "age", "ratio",
]
ERROR_FIELDS = ["error_e", "error_n", "error_u", "error_h", "error_3d"]


def load_truth():
    truth = {}
    with open(TRUTH_CSV) as f:
        for row in csv.DictReader(f):
            x, y, z = float(row["x_ecef_m"]), float(row["y_ecef_m"]), float(row["z_ecef_m"])
            lat, lon, _ = ecef2llh(x, y, z)
            truth[row["station"]] = (x, y, z, lat, lon)
    return truth


def parse_obs_epochs(obs_path):
    """Return the sorted list of epoch datetimes the receiver actually attempted."""
    epochs = []
    with open(obs_path) as f:
        for line in f:
            if line.startswith("> "):
                fields = line[1:].split()
                if len(fields) < 6:
                    continue
                year, month, day, hour, minute, sec = fields[:6]
                epochs.append(
                    datetime(int(year), int(month), int(day), int(hour), int(minute), int(float(sec)))
                )
    return sorted(epochs)


def parse_pos_file(pos_path):
    records = {}
    with open(pos_path) as f:
        for line in f:
            if line.startswith("%") or not line.strip():
                continue
            date_str, time_str, *rest = line.split()
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M:%S.%f").replace(microsecond=0)
            records[dt] = dict(zip(POS_COLUMNS, rest))
    return records


def build_timeline(station, day, obs_path, pos_path, truth):
    truth_x, truth_y, truth_z, truth_lat, truth_lon = truth[station]
    obs_epochs = parse_obs_epochs(obs_path)
    pos_records = parse_pos_file(pos_path)

    out_rows = []
    for epoch in obs_epochs:
        row = {"station": station, "day": day, "time": epoch.isoformat(), "solution_exists": epoch in pos_records}
        rec = pos_records.get(epoch)
        if rec is not None:
            lat, lon, height = float(rec["lat"]), float(rec["lon"]), float(rec["height"])
            x, y, z = llh2ecef(lat, lon, height)
            e, n, u = ecef_diff_to_enu(x - truth_x, y - truth_y, z - truth_z, truth_lat, truth_lon)
            row.update(rec)
            row.update(
                error_e=e, error_n=n, error_u=u,
                error_h=(e**2 + n**2) ** 0.5, error_3d=(e**2 + n**2 + u**2) ** 0.5,
            )
        else:
            row.update({k: "" for k in POS_COLUMNS + ERROR_FIELDS})
        out_rows.append(row)
    return out_rows


def main():
    truth = load_truth()
    PROCESSED.mkdir(parents=True, exist_ok=True)

    for station in sorted(truth):
        for pos_path in sorted((INTERIM / station).glob("*/spp.pos")):
            day = pos_path.parent.name
            obs_candidates = [p for p in pos_path.parent.glob("*.rnx") if not p.name.startswith(("BRDC", "BRDM"))]
            if not obs_candidates:
                print(f"SKIP {station} {day}: no observation RINEX found")
                continue
            obs_path = obs_candidates[0]

            rows = build_timeline(station, day, obs_path, pos_path, truth)
            out_csv = PROCESSED / f"mgex_{station}_{day}_error.csv"
            with open(out_csv, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

            n_solved = sum(1 for r in rows if r["solution_exists"])
            horiz = [r["error_h"] for r in rows if r["solution_exists"]]
            horiz_sorted = sorted(horiz)
            p95 = horiz_sorted[int(0.95 * len(horiz_sorted))]
            print(
                f"{station} {day}: {len(rows)} full-timeline epochs, {n_solved} with a solution "
                f"({100 * n_solved / len(rows):.1f}%) mean_h={statistics.mean(horiz):.2f}m "
                f"median_h={statistics.median(horiz):.2f}m p95_h={p95:.2f}m max_h={max(horiz):.2f}m "
                f"-> {out_csv.relative_to(ROOT)}"
            )


if __name__ == "__main__":
    main()
