"""Trust-classification metrics (redraft PUBLISHABLE_PROJECT_REDRAFT.md §11).

Shared between rule-gate evaluation (Stage 4) and ML classifier evaluation
(Stage 5) — one definition, used everywhere, rather than each stage
recomputing these from scratch.
"""


def compute_metrics(predicted_trust, actual_trust):
    """predicted_trust, actual_trust: boolean Series/arrays, same length.
    True = TRUST.
    """
    predicted_trust = predicted_trust.astype(bool)
    actual_trust = actual_trust.astype(bool)

    actual_unsafe = ~actual_trust
    predicted_unsafe = ~predicted_trust

    n_actual_unsafe = actual_unsafe.sum()
    n_actual_safe = actual_trust.sum()
    n_predicted_unsafe = predicted_unsafe.sum()

    true_positive_unsafe = (predicted_unsafe & actual_unsafe).sum()  # correctly flagged unsafe
    missed_unsafe = (predicted_trust & actual_unsafe).sum()          # trusted but actually unsafe
    false_alarm = (predicted_unsafe & actual_trust).sum()            # flagged unsafe but actually safe

    unsafe_recall = true_positive_unsafe / n_actual_unsafe if n_actual_unsafe else float("nan")
    missed_unsafe_rate = missed_unsafe / n_actual_unsafe if n_actual_unsafe else float("nan")
    false_alarm_rate = false_alarm / n_actual_safe if n_actual_safe else float("nan")
    unsafe_precision = true_positive_unsafe / n_predicted_unsafe if n_predicted_unsafe else float("nan")

    if unsafe_precision + unsafe_recall > 0 and n_actual_unsafe and n_predicted_unsafe:
        f1_unsafe = 2 * unsafe_precision * unsafe_recall / (unsafe_precision + unsafe_recall)
    else:
        f1_unsafe = float("nan")

    safe_recall = 1 - false_alarm_rate if n_actual_safe else float("nan")
    balanced_accuracy = (
        (unsafe_recall + safe_recall) / 2
        if n_actual_unsafe and n_actual_safe
        else float("nan")
    )
    trust_availability = predicted_trust.mean()

    return {
        "unsafe_recall": unsafe_recall,
        "missed_unsafe_rate": missed_unsafe_rate,
        "false_alarm_rate": false_alarm_rate,
        "unsafe_precision": unsafe_precision,
        "f1_unsafe": f1_unsafe,
        "balanced_accuracy": balanced_accuracy,
        "trust_availability": trust_availability,
        "n_epochs": len(actual_trust),
        "n_actual_unsafe": int(n_actual_unsafe),
    }
