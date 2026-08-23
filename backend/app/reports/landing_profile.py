# ============================================================
# landing_profile.py — the simple, always-4-categories summary of a
# landing: Knee Control, Landing Depth, Symmetry, Trunk Control. This is
# the "don't overwhelm with raw numbers first" view — the technical
#17-item LESS breakdown and full metric grid stay available on the
# report page, just not the first thing shown.
#
# WHY THESE FOUR, AND WHY THEY'RE THE SAME ONES priorities.py FLAGS:
# knee_control/landing_depth/symmetry/trunk_control are exactly
# frontal_knee_control/knee_flexion/symmetry/trunk_control from
# exercises/priorities.py's MovementTarget vocabulary — reusing that
# mapping instead of inventing a second one is deliberate. The
# difference is what priorities.py does with it: priorities.py surfaces
# only what's FLAGGED (severity > 0, top 3), because that's what an
# exercise recommendation needs. This module rates all four ALWAYS, even
# when everything looks fine, because that's what a summary needs.
#
# RATING VOCABULARY MATCHES Metric.status (ok/watch/flag) rather than
# inventing new words like "good"/"needs attention" — one banding
# vocabulary for the whole app, not two that mean the same thing.
# "unavailable" is a necessary fifth state: a single-view session can't
# rate every category (e.g. landing_depth needs a side clip).
# ============================================================

from dataclasses import dataclass
from typing import Literal

from app.exercises.priorities import LESS_KEY_TO_TARGETS, METRIC_KEY_TO_TARGETS
from app.models.schemas import Metric
from app.risk.less import LessItemScore

Rating = Literal["ok", "watch", "flag", "unavailable"]

CATEGORY_TARGET = {
    "knee_control": "frontal_knee_control",
    "landing_depth": "knee_flexion",
    "symmetry": "symmetry",
    "trunk_control": "trunk_control",
}

CATEGORY_LABEL = {
    "knee_control": "Knee control",
    "landing_depth": "Landing depth",
    "symmetry": "Symmetry",
    "trunk_control": "Trunk control",
}

# Which raw measurement keys are eligible to represent each category,
# in preference order (used only to break ties when more than one is
# present with the same status — see _pick_representative below).
CATEGORY_METRIC_CANDIDATES: dict[str, list[str]] = {
    "knee_control": ["knee_valgus_left", "knee_valgus_right", "kasr", "knee_valgus"],
    "landing_depth": ["knee_flexion_left", "knee_flexion_right", "knee_flexion"],
    "symmetry": ["valgus_asymmetry", "flexion_asymmetry", "asymmetry"],
    "trunk_control": ["trunk_lean_lateral", "trunk_lean_forward", "trunk_lean"],
}

_STATUS_RANK = {"flag": 2, "watch": 1, "ok": 0}

_EXPLANATIONS: dict[str, dict[Rating, str]] = {
    "knee_control": {
        "flag": "Your knee moved inward relative to your hip and ankle during the landing.",
        "watch": "Your knee position was borderline, a little inward motion relative to your hip and ankle.",
        "ok": "Your knee tracked well over your hip and ankle during the landing.",
        "unavailable": "Needs a front-view clip to measure.",
    },
    "landing_depth": {
        "flag": "Your landing looked stiff, with limited knee bend to absorb the impact.",
        "watch": "Your knee bend on landing was a little shallow.",
        "ok": "Your knees bent substantially as you absorbed the landing.",
        "unavailable": "Needs a side-view clip to measure.",
    },
    "symmetry": {
        "flag": "Your two sides showed a large difference during landing.",
        "watch": "Your two sides showed a measurable difference during landing.",
        "ok": "Your left and right sides landed evenly.",
        "unavailable": "Needs a clear view of both legs to measure.",
    },
    "trunk_control": {
        "flag": "Your trunk leaned noticeably during the landing.",
        "watch": "Your trunk showed a bit of lean during the landing.",
        "ok": "Your trunk stayed controlled and upright during the landing.",
        "unavailable": "Needs a clip to measure.",
    },
}

_FRONT_VIEW_KEYS = {"knee_valgus_left", "knee_valgus_right", "kasr", "knee_valgus", "valgus_asymmetry", "trunk_lean_lateral"}
_SIDE_VIEW_KEYS = {"knee_flexion_left", "knee_flexion_right", "knee_flexion", "flexion_asymmetry", "trunk_lean_forward", "trunk_lean"}


@dataclass(frozen=True)
class LandingProfileCategory:
    category: str            # e.g. "knee_control"
    label: str                # e.g. "Knee control"
    rating: Rating
    value: float | None       # the representative measurement, if any
    unit: str | None
    metric_label: str | None  # e.g. "Knee valgus, left"
    explanation: str
    source_view: str | None   # "front" / "side" / None


@dataclass(frozen=True)
class LandingProfile:
    categories: list[LandingProfileCategory]


def _pick_representative(category: str, metrics_by_key: dict[str, Metric]) -> Metric | None:
    candidates = [metrics_by_key[k] for k in CATEGORY_METRIC_CANDIDATES[category] if k in metrics_by_key]
    if not candidates:
        return None
    # Worst status wins; ties broken by candidate-list order (already
    # reflected in `candidates`' order since we built it in that order).
    return max(candidates, key=lambda m: _STATUS_RANK.get(m.status, 0))


def _less_items_for_target(target: str, less_items: list[LessItemScore]) -> list[LessItemScore]:
    return [item for item in less_items if target in LESS_KEY_TO_TARGETS.get(item.key, [])]


def _source_view(metric_key: str | None) -> str | None:
    if metric_key is None:
        return None
    if metric_key in _FRONT_VIEW_KEYS:
        return "front"
    if metric_key in _SIDE_VIEW_KEYS:
        return "side"
    return None


def compute_landing_profile(
    metrics_list: list[Metric],
    less_items: list[LessItemScore],
) -> LandingProfile:
    """
    Rate all four categories for one analysis — always four, never fewer,
    with "unavailable" as an honest result rather than omitting a
    category a single-view session couldn't measure.
    """
    metrics_by_key = {m.key: m for m in metrics_list}
    categories: list[LandingProfileCategory] = []

    for category, target in CATEGORY_TARGET.items():
        representative = _pick_representative(category, metrics_by_key)
        matching_less = _less_items_for_target(target, less_items)
        any_less_flagged = any(item.points > 0 for item in matching_less)

        if any_less_flagged:
            rating: Rating = "flag"
        elif representative is not None and representative.status == "flag":
            rating = "flag"
        elif representative is not None and representative.status == "watch":
            rating = "watch"
        elif representative is not None or matching_less:
            rating = "ok"
        else:
            rating = "unavailable"

        categories.append(
            LandingProfileCategory(
                category=category,
                label=CATEGORY_LABEL[category],
                rating=rating,
                value=representative.value if representative else None,
                unit=representative.unit if representative else None,
                metric_label=representative.label if representative else None,
                explanation=_EXPLANATIONS[category][rating],
                source_view=_source_view(representative.key if representative else None),
            )
        )

    return LandingProfile(categories=categories)
