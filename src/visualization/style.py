"""Single source of truth for figure styling.

Every figure-generation script in this project imports its colors and rcParams
from here rather than choosing them locally — see CLAUDE.md section 8 for the
palette-validation rationale (Okabe-Ito derived, minus the two slots that fail
computational colorblind/contrast checks).
"""

import matplotlib as mpl

CATEGORICAL = [
    "#0072B2",  # blue
    "#E69F00",  # orange
    "#009E73",  # bluish green
    "#CC79A7",  # reddish purple
    "#D55E00",  # vermillion
    "#56B4E9",  # sky blue
]

REFERENCE_COLOR = "#333333"
NO_SOLUTION_COLOR = "#B0B0B0"
MARK_EDGECOLOR = "#000000"
SEQUENTIAL_CMAP = "viridis"


def get_categorical_colors(n):
    """Return the first `n` fixed-order categorical colors.

    Parameters
    ----------
    n : int
        Number of series needed. Must not exceed len(CATEGORICAL) — a 7th
        series should fold into "other" or a separate small-multiple, not
        extend this list.

    Returns
    -------
    list of str
        Hex colors, same order every time a given n is requested.
    """
    if n > len(CATEGORICAL):
        raise ValueError(
            f"requested {n} categorical colors but only {len(CATEGORICAL)} "
            "validated slots exist (CLAUDE.md section 8) — reduce series "
            "count or use small multiples instead of adding colors"
        )
    return CATEGORICAL[:n]


def apply_style():
    """Set shared matplotlib rcParams for every figure in this project."""
    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 600,
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "lines.linewidth": 2,
            "patch.edgecolor": MARK_EDGECOLOR,
            "patch.linewidth": 0.8,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "savefig.format": "tiff",
        }
    )


def add_panel_label(ax, label):
    """Add a bold uppercase panel label (A, B, C, …) at a subplot's top-left.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    label : str
        A single letter, e.g. "A".
    """
    ax.text(
        -0.12,
        1.05,
        label,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        va="bottom",
        ha="right",
    )
