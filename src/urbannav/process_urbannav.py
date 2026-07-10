"""Drive BDS-only RTKLIB SPP processing for the UrbanNav kinematic sequences,
using the receiver designated in configs/project_config.yaml.

Run as a script: `python -m src.urbannav.process_urbannav` from the repo root.
"""

from pathlib import Path

from src.rtklib.run_spp import run_spp

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "urbannav"
INTERIM = ROOT / "data" / "interim" / "urbannav"

RECEIVER = "ublox.m8t.GC"  # see configs/project_config.yaml
SEQUENCES = {
    "tunnel_1": "20210518.tunnel.cht.ublox.m8t.GC.obs",
    "deep_urban_1": "UrbanNav-HK-Deep-Urban-1.ublox.m8t.GC.obs",
}


def main():
    for sequence, obs_filename in SEQUENCES.items():
        obs_path = RAW / sequence / "obs" / obs_filename
        nav_paths = sorted((RAW / sequence / "nav").glob("*"))
        if not obs_path.exists() or not nav_paths:
            print(f"SKIP {sequence}: missing obs or nav")
            continue

        out_pos = INTERIM / sequence / "spp.pos"
        run_spp(obs_path, nav_paths, out_pos)
        n_epochs = sum(1 for line in open(out_pos) if line and not line.startswith("%"))
        print(f"OK {sequence}: {n_epochs} solution epochs -> {out_pos}")


if __name__ == "__main__":
    main()
