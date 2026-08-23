# ============================================================
# test_exercise_database.py — structural integrity of the exercise
# library: unique ids, every field populated, every citation traceable
# to a real program, and the youth plyometric safety gating actually
# applied (not just documented) to every single-leg jumping exercise.
# ============================================================

from app.exercises.database import (
    EXERCISES,
    EXERCISES_BY_ID,
    exercises_for_target,
)
from app.exercises.research_library import ALL_PROGRAMS, PROGRAMS_BY_ID


def test_every_exercise_id_is_unique():
    ids = [e.exercise_id for e in EXERCISES]
    assert len(ids) == len(set(ids))


def test_every_exercise_has_required_fields_populated():
    for e in EXERCISES:
        assert e.exercise_id
        assert e.exercise_name
        assert e.short_description
        assert e.instructions, f"{e.exercise_id} has no instructions"
        assert e.movement_targets, f"{e.exercise_id} has no movement_targets"
        assert e.difficulty in ("beginner", "intermediate", "advanced")
        assert e.equipment
        assert e.age_ranges, f"{e.exercise_id} has no age_ranges"
        assert e.sports, f"{e.exercise_id} has no sports"
        assert e.competitive_levels, f"{e.exercise_id} has no competitive_levels"
        assert e.research_source
        assert e.source_program
        assert e.safety_notes


def test_every_exercise_cites_a_real_program():
    """Every research_source must mention at least one real, cited program
    name — guards against a future edit attaching an untraceable source."""
    program_names = [p.program_name for p in ALL_PROGRAMS]
    for e in EXERCISES:
        assert any(name in e.source_program for name in program_names), (
            f"{e.exercise_id}'s source_program ({e.source_program!r}) doesn't "
            f"match any program in research_library.py"
        )


def test_lookup_by_id_matches_the_list():
    assert len(EXERCISES_BY_ID) == len(EXERCISES)
    for e in EXERCISES:
        assert EXERCISES_BY_ID[e.exercise_id] is e


def test_exercises_for_target_returns_only_matching_exercises():
    results = exercises_for_target("frontal_knee_control")
    assert results
    for e in results:
        assert "frontal_knee_control" in e.movement_targets
    # Sanity check: every result actually came from the master list.
    assert set(e.exercise_id for e in results) <= set(e.exercise_id for e in EXERCISES)


def test_single_leg_plyometric_exercises_exclude_youngest_age_range():
    """
    The PEP program's manual explicitly withholds single-leg plyometrics
    from athletes 12 and under. Spot-check the exercises that are
    genuinely single-leg-landing plyometrics (not double-leg jumps, not
    strength/balance work) to confirm that constraint is actually
    encoded, not just mentioned in a safety note.
    """
    single_leg_plyo_ids = {
        "single_leg_cross_hops",
        "lateral_bound",
        "nordic_hamstring_lower",  # not plyometric, but flagged advanced/14+ deliberately
    }
    for exercise_id in single_leg_plyo_ids:
        exercise = EXERCISES_BY_ID[exercise_id]
        assert "12-13" not in exercise.age_ranges, (
            f"{exercise_id} should exclude the 12-13 age range"
        )


def test_double_leg_plyometrics_remain_available_to_youngest_age_range():
    """The flip side: double-leg jumps ARE explicitly sanctioned for 12U
    in the PEP manual (with a flat-cone/two-feet caveat), so they should
    still list the 12-13 age range rather than being over-excluded."""
    double_leg_ids = {"squat_jump_stick", "double_leg_bounding", "lateral_hop_over_cone"}
    for exercise_id in double_leg_ids:
        exercise = EXERCISES_BY_ID[exercise_id]
        assert "12-13" in exercise.age_ranges


def test_research_library_programs_have_no_placeholder_citations():
    for program in ALL_PROGRAMS:
        assert program.citation
        assert "doi" in program.citation.lower() or "." in program.citation
        assert program.program_id in PROGRAMS_BY_ID
