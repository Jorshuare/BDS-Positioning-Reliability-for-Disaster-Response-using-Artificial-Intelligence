# GNSS Trust Classification for Disaster-Response Robot Navigation

Real-time trust classification for standalone BeiDou (BDS) GNSS positioning, aimed at disaster-response robot navigation. Rather than predicting exact positioning error, the system decides at each epoch whether the current BeiDou single-point-positioning (SPP) solution should be trusted, or whether the robot should fall back to another localization source (IMU, vision, LiDAR, wheel odometry, map matching).

Rule-based trust gates and machine-learning classifiers (logistic regression, random forest, LightGBM) are compared against each other, validated across clean static reference stations and harsh kinematic urban-canyon data.

## Data

Not included in this repository. The pipeline expects:

- **MGEX static stations** (JFNG, URUM, HKWS): RINEX observation + broadcast navigation files, placed under `data/raw/mgex/`, plus a station truth-coordinate source under `data/external/`.
- **UrbanNav kinematic sequences** (Tunnel-1, Deep-Urban-1): observation, navigation, and ground-truth trajectory files, placed under `data/raw/urbannav/<sequence>/`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Also requires [RTKLIB](https://www.rtklib.com/) (`rnx2rtkp`) available on `PATH`.

## Project layout

```
data/
  raw/          # RINEX obs/nav, UrbanNav ground truth (not tracked)
  external/     # station truth coordinates and other reference data (not tracked)
  interim/      # RTKLIB SPP output per station/sequence (not tracked)
  processed/    # labeled, feature-engineered tables ready for modeling (not tracked)
src/
  common/       # shared utilities (data intake verification, geodesy helpers)
  rtklib/       # BeiDou-only SPP processing
  urbannav/     # UrbanNav-specific processing and labeling
  labels/       # trust-label construction and rule-based gates
  models/       # ML classifiers and evaluation
  visualization/  # shared figure styling and plotting
configs/        # run configuration (RTKLIB config, project-wide decisions)
reports/        # generated verification/analysis reports
results/
  tables/       # metric tables
  figures/      # generated figures
references/     # data dictionaries, source citations, external documentation
```

## Method summary

1. Process raw observations with RTKLIB, restricted to BeiDou-only single-point positioning.
2. Extract per-epoch measurement-level features (satellite count, receiver uncertainty, C/N0 statistics, elevation/azimuth statistics, pseudorange residuals) and causal rolling-window temporal features.
3. Label each epoch trustworthy or untrustworthy against a configurable horizontal-error threshold, with no-solution epochs always treated as untrustworthy.
4. Compare a fixed-threshold rule gate, a data-tuned rule gate, and logistic regression / random forest / LightGBM classifiers.
5. Evaluate with metrics suited to a rare, safety-relevant class: unsafe recall, missed-unsafe rate, false-alarm rate, and trust availability — across leave-one-station-out, cross-domain, and mixed-domain validation splits.

## License

Not yet specified.
