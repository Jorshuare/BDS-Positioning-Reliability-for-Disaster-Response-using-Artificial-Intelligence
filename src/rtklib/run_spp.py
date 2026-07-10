"""Run RTKLIB `rnx2rtkp` for BeiDou-only standalone SPP.

Positioning mode, elevation mask, and solution-status output level are passed
as CLI flags (documented, version-stable); everything else (navigation-system
restriction, tropo/iono models) comes from configs/rtklib_bds_spp.conf.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs" / "rtklib_bds_spp.conf"


def run_spp(obs_path, nav_paths, out_pos_path, elevation_mask_deg=10):
    """Run rnx2rtkp for one observation file against one or more nav files.

    Parameters
    ----------
    obs_path : Path
        Plain RINEX observation file (already decompressed).
    nav_paths : list of Path
        One or more plain RINEX navigation files.
    out_pos_path : Path
        Where to write the `.pos` solution file; a matching `.stat` file
        (per-satellite az/el/C-N0/residuals) is written alongside it.
    elevation_mask_deg : float
        Elevation mask angle in degrees (redraft/CLAUDE.md default: 10).

    Returns
    -------
    Path
        `out_pos_path`, once rnx2rtkp has run.
    """
    out_pos_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "rnx2rtkp",
        "-k", str(CONFIG),
        "-p", "0",  # single (standalone SPP)
        "-m", str(elevation_mask_deg),
        "-y", "2",  # solution status: residuals ($SAT records incl. az/el/C-N0/residual)
        "-o", str(out_pos_path),
        str(obs_path),
        *[str(p) for p in nav_paths],
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"rnx2rtkp failed (exit {result.returncode}) for {obs_path}:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return out_pos_path
