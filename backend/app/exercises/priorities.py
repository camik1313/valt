# ============================================================
# priorities.py — turns a completed scan's LESS score and raw
# measurements into the athlete's top 1-3 modifiable movement
# priorities, in the small vocabulary defined in database.py
# (MovementTarget), so the ranking engine (ranking.py) has something
# concrete to match exercises against.
#
# WHY THIS EXISTS SEPARATELY FROM ranking.py: detecting "what's wrong"
# and deciding "what to recommend for it" are different jobs. Keeping
# them apart means either one can be tested, and reasoned about, on its
# own — the same separation risk/less.py (scoring) and risk/scoring.py
# (a different score) already keep from report_service.py (assembly).
#
# TWO SIGNALS, EITHER ONE IS ENOUGH: a LESS item scoring points is a
# validated clinical flag; a raw measurement landing in "watch" or
# "flag" territory (report_service.py's banding) is a second, less
# formal signal covering ground LESS doesn't reach with a single-view
# session. For a given movement target, this takes whichever signal is
# STRONGER rather than averaging them — diluting a real flag with a
# vaguer secondary signal would understate it, not add precision.
#
# NOT USED: the screening risk score (risk/scoring.py). That composite
# is a separate, less rigorously grounded score than LESS and this
# module deliberately doesn't lean on it for something as consequential
# as "what should this athlete work on."
# ============================================================

from dataclasses import dataclass

from app.exercises.database import MovementTarget
from app.risk.less import LessItemScore

# Every scored LESS item, mapped to the movement target(s) it's evidence
# for. Items not covering ground meaningfully distinct from another
# target's items are mapped once, to their closest single match, rather
# than fanned out to several targets and diluting the signal.
LESS_KEY_TO_TARGETS: dict[str, list[MovementTarget]] = {
    "knee_flexion_ic": ["knee_flexion"],
    "hip_flexion_ic": ["landing_control"],
    "trunk_flexion_ic": ["trunk_control"],
    "knee_flexion_displacement": ["knee_flexion"],
    "hip_flexion_displacement": ["landing_control"],
    "trunk_flexion_displacement": ["trunk_control"],
    "ankle_plantarflexion_ic": ["landing_control"],
    "foot_contact_symmetry": ["symmetry"],
    "trunk_lateral_ic": ["trunk_control"],
    "knee_valgus_ic": ["frontal_knee_control"],
    "stance_width_narrow": ["frontal_knee_control"],
    "stance_width_wide": ["frontal_knee_control"],
    "foot_ir_max_flexion": ["frontal_knee_control"],
    "foot_er_max_flexion": ["frontal_knee_control"],
    "knee_valgus_displacement": ["frontal_knee_control"],
    "joint_displacement": ["landing_control"],
    "overall_impression": ["landing_control"],
}

# Raw measurement keys (report_service.py's DISPLAY_ORDER), mapped the
# same way, for the "watch"/"flag" banding signal.
METRIC_KEY_TO_TARGETS: dict[str, list[MovementTarget]] = {
    "knee_valgus_left": ["frontal_knee_control"],
    "knee_valgus_right": ["frontal_knee_control"],
    "valgus_asymmetry": ["symmetry"],
    "kasr": ["frontal_knee_control"],
    "trunk_lean_lateral": ["trunk_control"],
    "knee_flexion_left": ["knee_flexion"],
    "knee_flexion_right": ["knee_flexion"],
    "hip_flexion_left": ["landing_control"],
    "hip_flexion_right": ["landing_control"],
    "flexion_asymmetry": ["symmetry"],
    "trunk_lean_forward": ["trunk_control"],
}

TARGET_LABELS: dict[MovementTarget, str] = {
    "landing_control": "landing control",
    "frontal_knee_control": "frontal knee control",
    "knee_flexion": "landing knee flexion",
    "trunk_control": "trunk control",
    "symmetry": "left/right symmetry",
    "hip_strength": "hip strength",
    "hamstring_strength": "hamstring strength",
    "calf_ankle_strength": "calf and ankle strength",
    "core_stability": "core stability",
    "balance": "balance",
    "deceleration": "deceleration control",
}

_METRIC_STATUS_WEIGHT = {"flag": 1.0, "watch": 0.5, "ok": 0.0}


@dataclass(frozen=True)
class MovementPriority:
    target: MovementTarget
    severity: float          # 0..1, how strongly this was flagged
    evidence: list[str]      # plain-language reasons, strongest first


def detect_priorities(
    less_items: list[LessItemScore],
    metric_status: dict[str, str],
    max_priorities: int = 3,
) -> list[MovementPriority]:
    """
    Rank the athlete's modifiable movement targets by how strongly this
    scan's evidence flags each one, and return the top `max_priorities`
    with severity > 0 — never pads the list with unflagged targets just
    to reach a count.

    `less_items`: this session's LessResult.items (risk/less.py).
    `metric_status`: metric key -> "ok"/"watch"/"flag", e.g. built from
        report_service.py's metrics_list as {m.key: m.status for m in metrics_list}.
    """
    severities: dict[MovementTarget, float] = {}
    evidence: dict[MovementTarget, list[str]] = {}

    def _record(target: MovementTarget, value: float, reason: str) -> None:
        if value <= 0:
            return
        if value > severities.get(target, 0.0):
            severities[target] = value
        evidence.setdefault(target, []).append(reason)

    for item in less_items:
        if item.max_points <= 0:
            continue
        fraction = item.points / item.max_points
        if fraction <= 0:
            continue
        for target in LESS_KEY_TO_TARGETS.get(item.key, []):
            _record(target, fraction, f"LESS: {item.label} was flagged.")

    for metric_key, status in metric_status.items():
        weight = _METRIC_STATUS_WEIGHT.get(status, 0.0)
        if weight <= 0:
            continue
        for target in METRIC_KEY_TO_TARGETS.get(metric_key, []):
            _record(target, weight, f"Measured: {metric_key.replace('_', ' ')} was {status}.")

    priorities = [
        MovementPriority(target=t, severity=round(s, 3), evidence=evidence[t])
        for t, s in severities.items()
    ]
    priorities.sort(key=lambda p: p.severity, reverse=True)
    return priorities[:max_priorities]
