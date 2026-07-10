"""Stage 1 data-intake verification.

Scans data/raw/ for the MGEX static-station and UrbanNav kinematic inputs
this project needs, and writes a manifest to reports/stage1_intake_manifest.md
reporting what's present, what's missing, and where BeiDou (system 'C')
observations were actually found — rather than assuming any of it.

Run as a script: `python -m src.common.verify_intake` from the repo root
(with .venv activated).
"""

import gzip
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
EXTERNAL = ROOT / "data" / "external"
REPORT_PATH = ROOT / "reports" / "stage1_intake_manifest.md"

MGEX_STATIONS = ["JFNG", "URUM", "HKWS"]
URBANNAV_SEQUENCES = ["tunnel_1", "deep_urban_1"]

OBS_FILENAME_RE = re.compile(r"_(\d{4})(\d{3})\d{4}_01D")


def _day_key(filename):
    """Extract (year, doy) from an MGEX-style RINEX filename, or None."""
    m = OBS_FILENAME_RE.search(filename)
    return (m.group(1), m.group(2)) if m else None


def _rinex_systems(path):
    """Return the set of RINEX observation-system letters in a file's header.

    Handles plain RINEX obs files directly, and Hatanaka+gzip (.crx.gz)
    MGEX files by decompressing to a temp file first.
    """
    if path.suffix == ".gz" and path.stem.endswith(".crx"):
        with tempfile.TemporaryDirectory() as tmp:
            crx_path = Path(tmp) / "in.crx"
            with gzip.open(path, "rb") as src, open(crx_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            subprocess.run(
                ["crx2rnx", str(crx_path), "-f"],
                cwd=tmp,
                check=True,
                capture_output=True,
            )
            rnx_path = crx_path.with_suffix(".rnx")
            text = rnx_path.read_text(errors="ignore")
    else:
        text = path.read_text(errors="ignore")

    systems = set()
    for line in text.splitlines():
        if "SYS / # / OBS TYPES" in line:
            systems.add(line.split()[0])
        if "END OF HEADER" in line:
            break
    return systems


def check_mgex():
    lines = ["## MGEX static stations", ""]
    ok = True
    nav_days = set()
    nav_dir = RAW / "mgex" / "nav"
    if nav_dir.is_dir():
        for f in nav_dir.glob("*.rnx.gz"):
            k = _day_key(f.name)
            if k:
                nav_days.add(k)
    lines.append(f"Broadcast nav files present for day(s): {sorted(nav_days) or 'NONE'}")
    lines.append("")

    for station in MGEX_STATIONS:
        st_dir = RAW / "mgex" / "obs" / station
        files = sorted(st_dir.glob("*.crx.gz")) if st_dir.is_dir() else []
        if not files:
            lines.append(f"- **{station}**: MISSING — no observation files found")
            ok = False
            continue
        for f in files:
            k = _day_key(f.name)
            nav_present = k in nav_days if k else False
            systems = _rinex_systems(f)
            bds = "C" in systems
            status = "OK" if (nav_present and bds) else "BLOCKED"
            if status == "BLOCKED":
                ok = False
            reason = []
            if not nav_present:
                reason.append("no matching broadcast nav for this day")
            if not bds:
                reason.append("no BeiDou (C) observations in header")
            reason_str = f" ({'; '.join(reason)})" if reason else ""
            lines.append(
                f"- **{station}** day {k[1] if k else '?'}/{k[0] if k else '?'}: "
                f"{status}{reason_str} — systems present: {sorted(systems)}"
            )

    lines.append("")
    truth_files = list(EXTERNAL.glob("*")) if EXTERNAL.is_dir() else []
    if truth_files:
        lines.append(f"Station truth-coordinate source found in data/external/: {[p.name for p in truth_files]}")
    else:
        lines.append(
            "**BLOCKING: no station truth-coordinate source found in data/external/.** "
            "MGEX horizontal/vertical error cannot be computed without it — "
            "an ITRF/IGS coordinate product (or equivalent) for JFNG, URUM, HKWS is needed here."
        )
        ok = False

    return ok, lines


def check_urbannav():
    lines = ["## UrbanNav kinematic sequences", ""]
    ok = True
    for seq in URBANNAV_SEQUENCES:
        seq_dir = RAW / "urbannav" / seq
        lines.append(f"### {seq}")

        nav_files = list((seq_dir / "nav").glob("*")) if (seq_dir / "nav").is_dir() else []
        lines.append(f"- nav: {[p.name for p in nav_files] or 'MISSING'}")
        if not nav_files:
            ok = False

        gt_files = list((seq_dir / "ground_truth").glob("*")) if (seq_dir / "ground_truth").is_dir() else []
        if gt_files:
            gt = gt_files[0]
            n_rows = sum(1 for _ in open(gt)) - 2
            lines.append(f"- ground truth: {gt.name} ({n_rows} data rows)")
        else:
            lines.append("- ground truth: MISSING")
            ok = False

        obs_dir = seq_dir / "obs"
        obs_files = sorted(obs_dir.glob("*.obs")) if obs_dir.is_dir() else []
        lines.append(f"- receiver logs found ({len(obs_files)}):")
        for f in obs_files:
            systems = _rinex_systems(f)
            bds_flag = "has BeiDou (C)" if "C" in systems else "no BeiDou"
            lines.append(f"  - `{f.name}` — systems {sorted(systems)} — **{bds_flag}**")
        lines.append("")

    lines.append(
        "**OPEN DECISION — not resolvable by inspection alone:** several receiver logs exist per "
        "sequence, and more than one contains BeiDou observations (see flags above). This project "
        "needs exactly one designated as \"the robot's receiver\" for BDS-only SPP processing — "
        "which one is a project decision, not a data fact."
    )
    return ok, lines


def main():
    mgex_ok, mgex_lines = check_mgex()
    urbannav_ok, urbannav_lines = check_urbannav()

    report = ["# Stage 1 — Data Intake Manifest", ""]
    report += mgex_lines + [""] + urbannav_lines
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report))

    print("\n".join(report))
    print()
    print(f"Manifest written to {REPORT_PATH.relative_to(ROOT)}")
    print(f"MGEX blocking issues: {'none' if mgex_ok else 'YES — see above'}")
    print(f"UrbanNav blocking issues: {'none' if urbannav_ok else 'YES — see above'}")


if __name__ == "__main__":
    main()
