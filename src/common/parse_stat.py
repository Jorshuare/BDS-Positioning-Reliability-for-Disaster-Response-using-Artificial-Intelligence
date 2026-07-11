"""Parse RTKLIB `.stat` per-satellite diagnostic records.

`$SAT,week,tow,sat,frq,az,el,resp,resc,vsat,snr,fix,slip,lock,outc,slipc,rejc`
one line per satellite per epoch. `vsat`/`fix`/`slip`/`lock` are RTK/carrier-
phase concepts that stay 0 in code-only single-point-positioning mode
regardless of whether the satellite was actually used — so aggregate stats
here are computed over every `$SAT` row at an epoch, not filtered by `vsat`.
"""

from datetime import datetime, timedelta

GPS_EPOCH = datetime(1980, 1, 6)


def parse_sat_records(stat_path):
    """Return {epoch_datetime: [{sat, frq, az, el, resp, snr}, ...]}."""
    epochs = {}
    with open(stat_path) as f:
        for line in f:
            if not line.startswith("$SAT"):
                continue
            fields = line.strip().split(",")
            week, tow = float(fields[1]), float(fields[2])
            # round to the nearest second (receiver clocks drift off-integer,
            # e.g. tow=...246.996) rather than truncate, to match how the
            # corresponding .pos epoch timestamps are rounded elsewhere.
            dt = GPS_EPOCH + timedelta(weeks=week, seconds=round(tow))
            epochs.setdefault(dt, []).append(
                {
                    "sat": fields[3],
                    "frq": fields[4],
                    "az": float(fields[5]),
                    "el": float(fields[6]),
                    "resp": float(fields[7]),
                    "snr": float(fields[10]),
                }
            )
    return epochs
