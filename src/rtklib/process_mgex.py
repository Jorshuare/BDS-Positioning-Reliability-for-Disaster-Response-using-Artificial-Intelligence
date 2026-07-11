"""Drive BDS-only RTKLIB SPP processing for all available MGEX station-days.

Uses exactly one broadcast navigation product per day: BRDC (the IGS combined
multi-GNSS broadcast ephemeris). BRDM (DLR's own combined broadcast product)
is available for the same days but deliberately not used — mixing two
overlapping ephemeris sources for the same satellites with no documented
selection rule is not a clean, reproducible experimental setup. BRDC is the
standard, most widely cited choice, and it's the only product UrbanNav ever
had anyway (single-source consistency across both domains).

Run as a script: `python -m src.rtklib.process_mgex` from the repo root.
"""

import re
from pathlib import Path

from src.common.rinex_io import ensure_decompressed
from src.rtklib.run_spp import run_spp

ROOT = Path(__file__).resolve().parents[2]
RAW_OBS = ROOT / "data" / "raw" / "mgex" / "obs"
RAW_NAV = ROOT / "data" / "raw" / "mgex" / "nav"
INTERIM = ROOT / "data" / "interim"

DAY_RE = re.compile(r"_(\d{4})(\d{3})\d{4}_01D")
NAV_PRODUCT = "BRDC"


def _day_key(filename):
    m = DAY_RE.search(filename)
    return (m.group(1), m.group(2)) if m else None


def main():
    stations = sorted(p.name for p in RAW_OBS.iterdir() if p.is_dir())
    processed = []
    for station in stations:
        for obs_file in sorted((RAW_OBS / station).glob("*.crx.gz")):
            year, doy = _day_key(obs_file.name)
            nav_files = [
                f for f in RAW_NAV.glob(f"{NAV_PRODUCT}*.rnx.gz")
                if _day_key(f.name) == (year, doy)
            ]
            if not nav_files:
                print(f"SKIP {station} {year}{doy}: no matching {NAV_PRODUCT} nav file")
                continue

            work_dir = INTERIM / station / f"{year}{doy}"
            obs_rnx = ensure_decompressed(obs_file, work_dir)
            nav_rnx = [ensure_decompressed(f, work_dir) for f in nav_files]

            out_pos = work_dir / "spp.pos"
            run_spp(obs_rnx, nav_rnx, out_pos)
            n_epochs = sum(
                1 for line in open(out_pos) if line and not line.startswith("%")
            )
            print(f"OK {station} {year}{doy}: {n_epochs} solution epochs -> {out_pos}")
            processed.append((station, year, doy, n_epochs))

    return processed


if __name__ == "__main__":
    main()
