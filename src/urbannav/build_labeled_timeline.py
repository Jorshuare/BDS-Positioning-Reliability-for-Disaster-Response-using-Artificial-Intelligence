"""Reconstruct the full 1 Hz UrbanNav epoch timeline from ground truth, and
join RTKLIB's BDS-only SPP solution onto it — epochs with no RTKLIB fix are
kept as explicit no-solution rows, not dropped, since they are exactly the
epochs a real-time trust monitor must learn to flag.

Run as a script: `python -m src.urbannav.build_labeled_timeline` from the repo root.
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path

from src.common.geodesy import ecef_diff_to_enu, llh2ecef

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "urbannav"
INTERIM = ROOT / "data" / "interim" / "urbannav"
PROCESSED = ROOT / "data" / "processed"

GPS_EPOCH = datetime(1980, 1, 6)
GT_FILENAMES = {
    "tunnel_1": "UrbanNav_tunnel_GT_raw.txt",
    "deep_urban_1": "UrbanNav_whampoa_raw.txt",
}
POS_COLUMNS = [
    "time", "lat", "lon", "height", "Q", "ns",
    "sdn", "sde", "sdu", "sdne", "sdeu", "sdun", "age", "ratio",
]


def dms_to_decimal(deg, minute, sec):
    sign = -1.0 if deg < 0 else 1.0
    return sign * (abs(deg) + minute / 60.0 + sec / 3600.0)


def parse_ground_truth(path):
    rows = []
    with open(path) as f:
        lines = f.readlines()[2:]  # skip the two header lines
    for line in lines:
        parts = line.split()
        if len(parts) < 19:
            continue
        week = float(parts[1])
        tow = float(parts[2])
        lat = dms_to_decimal(float(parts[3]), float(parts[4]), float(parts[5]))
        lon = dms_to_decimal(float(parts[6]), float(parts[7]), float(parts[8]))
        height = float(parts[9])
        gps_dt = GPS_EPOCH + timedelta(weeks=week, seconds=tow)
        rows.append({"gps_dt": gps_dt.replace(microsecond=0), "lat": lat, "lon": lon, "height": height})
    return rows


def parse_pos_file(path):
    records = {}
    with open(path) as f:
        for line in f:
            if line.startswith("%") or not line.strip():
                continue
            date_str, time_str, *rest = line.split()
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M:%S.%f")
            key = dt.replace(microsecond=0)
            if abs(dt.microsecond - 0) > 500000:
                key = key + timedelta(seconds=1)
            record = dict(zip(POS_COLUMNS, [None] + rest))
            records[key] = record
    return records


def build_timeline(sequence):
    gt_rows = parse_ground_truth(RAW / sequence / "ground_truth" / GT_FILENAMES[sequence])
    pos_records = parse_pos_file(INTERIM / sequence / "spp.pos")

    out_rows = []
    n_solved = 0
    for gt in gt_rows:
        rec = pos_records.get(gt["gps_dt"])
        row = {
            "gps_dt": gt["gps_dt"].isoformat(),
            "gt_lat": gt["lat"],
            "gt_lon": gt["lon"],
            "gt_height": gt["height"],
            "solution_exists": rec is not None,
        }
        if rec is not None:
            n_solved += 1
            x, y, z = llh2ecef(float(rec["lat"]), float(rec["lon"]), float(rec["height"]))
            gt_x, gt_y, gt_z = llh2ecef(gt["lat"], gt["lon"], gt["height"])
            e, n, u = ecef_diff_to_enu(x - gt_x, y - gt_y, z - gt_z, gt["lat"], gt["lon"])
            row.update(
                lat=rec["lat"], lon=rec["lon"], height=rec["height"],
                Q=rec["Q"], ns=rec["ns"], sdn=rec["sdn"], sde=rec["sde"], sdu=rec["sdu"],
                sdne=rec["sdne"], sdeu=rec["sdeu"], sdun=rec["sdun"],
                age=rec["age"], ratio=rec["ratio"],
                error_e=e, error_n=n, error_u=u,
                error_h=(e**2 + n**2) ** 0.5, error_3d=(e**2 + n**2 + u**2) ** 0.5,
            )
        else:
            row.update({k: "" for k in [
                "lat", "lon", "height", "Q", "ns", "sdn", "sde", "sdu",
                "sdne", "sdeu", "sdun", "age", "ratio",
                "error_e", "error_n", "error_u", "error_h", "error_3d",
            ]})
        out_rows.append(row)

    out_csv = PROCESSED / f"urbannav_{sequence}_error.csv"
    PROCESSED.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)

    print(
        f"{sequence}: {len(out_rows)} full-timeline epochs, "
        f"{n_solved} with a solution ({100 * n_solved / len(out_rows):.1f}%) -> "
        f"{out_csv.relative_to(ROOT)}"
    )
    solved_errors = [r["error_h"] for r in out_rows if r["solution_exists"]]
    if solved_errors:
        solved_errors.sort()
        print(
            f"  solved-epoch horizontal error: mean={sum(solved_errors)/len(solved_errors):.2f}m "
            f"median={solved_errors[len(solved_errors)//2]:.2f}m max={solved_errors[-1]:.2f}m"
        )


def main():
    for sequence in GT_FILENAMES:
        build_timeline(sequence)


if __name__ == "__main__":
    main()
