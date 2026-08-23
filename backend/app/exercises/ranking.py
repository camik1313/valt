# ============================================================
# ranking.py — turns movement priorities (priorities.py) into ranked,
# explained exercise recommendations from the verified library
# (database.py). No AI call here: this is the same kind of transparent,
# inspectable points formula as risk/scoring.py, applied to matching
# instead of screening.
#
# THE FORMULA, roughly matching the shape sketched in the product spec
# (deficit severity x exercise-target match x sport/age/level fit):
#
#   1. AGE, SPORT, COMPETITIVE LEVEL are HARD FILTERS, not soft
#      multipliers. Age in particular encodes a real safety constraint
#      (see database.py's youth plyometric gating) — an exercise that
#      doesn't fit the athlete's age has no business being ranked lower,
#      it has no business appearing at all.
#   2. Within the eligible set, an exercise's score is the sum of the
#      severities of every priority it addresses. An exercise matching
#      two flagged priorities outranks one matching only the athlete's
#      single biggest priority, which is the intended behavior: breadth
#      of relevance matters alongside severity.
#
# HONEST LIMITATION, stated once here rather than implied: every
# exercise in the current database (see database.py) lists the full
# jump/cut sport set and every competitive level — none of the source
# programs' materials differentiated by sport or level at the individual
# exercise level. SPORT does have real teeth today: an athlete whose
# specific sport isn't in that set (report_service.py maps "other" to
# None rather than filtering on it) would otherwise see every exercise
# excluded, so it's a genuine filter, just one that currently never
# excludes anything for a sport the app actually tracks. COMPETITIVE_LEVEL
# is still a no-op either way — every exercise matches every level — kept
# wired for when the database gains entries that differentiate by level.
#
# DOMINANT LEG is accepted as a parameter for the same forward-looking
# reason but currently unused, and not yet collected anywhere in the
# athlete intake either: no exercise in the database has a
# dominant-leg-specific variant, so there's nothing to rank on yet. Using
# it today would mean pretending to rank on data that doesn't exist.
# ============================================================

from dataclasses import dataclass

from app.exercises.database import (
    EXERCISES,
    AgeRange,
    CompetitiveLevel,
    Exercise,
    Sport,
)
from app.exercises.priorities import TARGET_LABELS, MovementPriority


@dataclass(frozen=True)
class RankedExercise:
    exercise: Exercise
    score: float
    matched_targets: list[str]
    why: str   # plain-language "why this was recommended"


def _build_why(exercise: Exercise, matched: list[MovementPriority]) -> str:
    target_names = ", ".join(TARGET_LABELS.get(p.target, p.target) for p in matched)
    lead_evidence = matched[0].evidence[0] if matched[0].evidence else ""
    return (
        f"Your scan flagged {target_names}. {lead_evidence} {exercise.short_description}"
    ).strip()


def rank_exercises(
    priorities: list[MovementPriority],
    age_range: AgeRange,
    sport: Sport | None = None,
    competitive_level: CompetitiveLevel | None = None,
    dominant_leg: str | None = None,   # accepted, currently unused — see module docstring
    top_n: int = 5,
) -> list[RankedExercise]:
    """
    Rank the exercise library against this athlete's detected movement
    priorities. Returns only exercises that match at least one priority
    — an exercise scoring 0 isn't a weak recommendation, it's not a
    recommendation, so it's excluded rather than padded in.
    """
    del dominant_leg  # not yet used; see module docstring

    eligible = [
        exercise
        for exercise in EXERCISES
        if age_range in exercise.age_ranges
        and (sport is None or sport in exercise.sports)
        and (competitive_level is None or competitive_level in exercise.competitive_levels)
    ]

    ranked: list[RankedExercise] = []
    for exercise in eligible:
        matched = [p for p in priorities if p.target in exercise.movement_targets]
        if not matched:
            continue
        score = round(sum(p.severity for p in matched), 3)
        ranked.append(
            RankedExercise(
                exercise=exercise,
                score=score,
                matched_targets=[p.target for p in matched],
                why=_build_why(exercise, matched),
            )
        )

    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked[:top_n]
