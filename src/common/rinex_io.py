"""Decompression helpers for RINEX files.

MGEX observation files ship Hatanaka-compressed and gzipped (.crx.gz);
MGEX/UrbanNav navigation files ship plain-gzipped (.rnx.gz); UrbanNav
observation files ship already as plain RINEX (.obs). `ensure_decompressed`
normalizes all three to a plain RINEX file under data/interim/, so
downstream stages never re-decompress the same input twice.
"""

import gzip
import shutil
import subprocess
from pathlib import Path

INTERIM_ROOT = Path(__file__).resolve().parents[2] / "data" / "interim"


def ensure_decompressed(path, dest_dir):
    """Return a plain-RINEX path for `path`, decompressing into `dest_dir` if needed.

    Parameters
    ----------
    path : Path
        Source file: `.crx.gz` (Hatanaka+gzip), `.gz` (plain gzip), or
        already-plain RINEX.
    dest_dir : Path
        Directory to write the decompressed file into (created if missing).

    Returns
    -------
    Path
        A plain RINEX file — `path` itself if no decompression was needed.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)

    if path.suffixes[-2:] == [".crx", ".gz"]:
        crx_path = dest_dir / path.with_suffix("").name  # strip .gz, keep .crx
        if not crx_path.exists():
            with gzip.open(path, "rb") as src, open(crx_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
        rnx_path = dest_dir / (crx_path.stem + ".rnx")
        if not rnx_path.exists():
            subprocess.run(
                ["crx2rnx", crx_path.name, "-f"],
                cwd=dest_dir,
                check=True,
                capture_output=True,
            )
        return rnx_path

    if path.suffix == ".gz":
        out_path = dest_dir / path.with_suffix("").name
        if not out_path.exists():
            with gzip.open(path, "rb") as src, open(out_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
        return out_path

    return path
