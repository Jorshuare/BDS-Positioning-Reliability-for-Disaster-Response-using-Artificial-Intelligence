"""Validation splits from PUBLISHABLE_PROJECT_REDRAFT.md §12 — all group-based
(by station/sequence), never a random row-level split, per the spatial/temporal
autocorrelation argument in CLAUDE.md §5.

Also implements the core-vs-temporal feature scoping decision (CLAUDE.md §5 /
PROGRESS.md Stage 3 post-sign-off): any split that includes more than one
domain drops the temporal/rolling-window columns, since they mean a different
real-world duration in each domain and would otherwise risk a spurious
domain-identity confound.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

MGEX_DATASETS = {
    "JFNG": ["mgex_JFNG_2023344", "mgex_JFNG_2023352"],
    "URUM": ["mgex_URUM_2023344", "mgex_URUM_2023352"],
    "HKWS": ["mgex_HKWS_2023352"],
}
URBANNAV_DATASETS = ["urbannav_tunnel_1", "urbannav_deep_urban_1"]

CORE_FEATURES = [
    "ns", "sdn", "sde", "sdu", "horiz_unc", "Q",
    "cn0_mean", "cn0_min", "cn0_max", "cn0_std",
    "el_mean", "el_min", "el_max", "az_std",
    "resp_mean", "resp_std", "resp_abs_max",
]
TEMPORAL_FEATURES = [
    c for c in [
        "position_jump_m", "consecutive_no_solution_epochs",
        *(f"{stat}_roll{w}s" for w in (3, 5, 10) for stat in (
            "cn0_mean", "cn0_min", "cn0_drop_rate", "resp_mean", "resp_max",
            "ns_min", "ns_change", "horiz_unc_growth",
        )),
    ]
]


def load_datasets(names, drop_temporal):
    """Load and concatenate named feature tables, tagging each row with its
    source dataset name so identity survives the concatenation.
    """
    frames = []
    for name in names:
        df = pd.read_csv(PROCESSED / f"features_{name}.csv")
        df["_dataset"] = name
        if drop_temporal:
            df = df.drop(columns=[c for c in TEMPORAL_FEATURES if c in df.columns])
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def loso_mgex_splits():
    """3 folds: train on 2 MGEX stations, test on the third."""
    for held_out in MGEX_DATASETS:
        train_names = [n for st, names in MGEX_DATASETS.items() if st != held_out for n in names]
        test_names = MGEX_DATASETS[held_out]
        yield f"loso_{held_out}", train_names, test_names, False  # single-domain: keep temporal cols (degenerate but harmless)


def cross_domain_split():
    """1 fold: train on all MGEX, test on both UrbanNav sequences."""
    train_names = [n for names in MGEX_DATASETS.values() for n in names]
    yield "mgex_to_urbannav", train_names, URBANNAV_DATASETS, True  # crosses domains: drop temporal cols


def mixed_domain_splits():
    """2 folds: train on all MGEX + one UrbanNav sequence, test on the other."""
    for i, seq in enumerate(URBANNAV_DATASETS):
        other = URBANNAV_DATASETS[1 - i]
        train_names = [n for names in MGEX_DATASETS.values() for n in names] + [seq]
        yield f"mixed_train_with_{seq}", train_names, [other], True  # crosses domains: drop temporal cols


def all_splits():
    yield from loso_mgex_splits()
    yield from cross_domain_split()
    yield from mixed_domain_splits()
