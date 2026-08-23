# ============================================================
# test_ranking.py — the exercise-ranking engine. Uses real exercise ids
# from database.py (not mocks) so these tests also double as a check
# that ranking behavior matches the actual shipped data.
# ============================================================

from app.exercises.priorities import MovementPriority
from app.exercises.ranking import rank_exercises


def _priority(target: str, severity: float) -> MovementPriority:
    return MovementPriority(target=target, severity=severity, evidence=[f"test evidence for {target}"])


def test_no_priorities_means_no_recommendations():
    assert rank_exercises(priorities=[], age_range="18+") == []


def test_matches_only_exercises_targeting_the_priority():
    priorities = [_priority("hamstring_strength", 1.0)]
    results = rank_exercises(priorities, age_range="18+")
    assert results
    for r in results:
        assert "hamstring_strength" in r.exercise.movement_targets


def test_age_filter_excludes_single_leg_plyometrics_for_youngest_bracket():
    """lateral_bound and single_leg_cross_hops are excluded from age_ranges
    for 12-13 per database.py's youth safety gating — ranking must respect
    that exclusion, not just the database's own field."""
    priorities = [_priority("frontal_knee_control", 1.0), _priority("balance", 1.0)]
    results_12_13 = rank_exercises(priorities, age_range="12-13")
    result_ids_12_13 = {r.exercise.exercise_id for r in results_12_13}
    assert "lateral_bound" not in result_ids_12_13
    assert "single_leg_cross_hops" not in result_ids_12_13

    results_16_17 = rank_exercises(priorities, age_range="16-17")
    result_ids_16_17 = {r.exercise.exercise_id for r in results_16_17}
    assert "lateral_bound" in result_ids_16_17 or "single_leg_cross_hops" in result_ids_16_17


def test_sport_filter_has_real_teeth():
    """No exercise in the current database lists 'other' as a sport, so
    filtering on it should exclude everything — confirms the filter
    actually runs rather than being a no-op."""
    priorities = [_priority("frontal_knee_control", 1.0)]
    results = rank_exercises(priorities, age_range="18+", sport="other")
    assert results == []

    results_soccer = rank_exercises(priorities, age_range="18+", sport="soccer")
    assert results_soccer


def test_dominant_leg_does_not_affect_results_yet():
    """No exercise in the current database has a dominant-leg-specific
    variant (see ranking.py's module docstring), so passing dominant_leg
    should be a pure no-op today. If this test ever fails, it means an
    exercise started varying by leg and this test needs updating
    alongside it — not that the no-op silently changed."""
    priorities = [_priority("frontal_knee_control", 1.0)]
    without_leg = rank_exercises(priorities, age_range="18+", top_n=50)
    with_leg = rank_exercises(priorities, age_range="18+", dominant_leg="left", top_n=50)
    assert [r.exercise.exercise_id for r in without_leg] == [r.exercise.exercise_id for r in with_leg]


def test_competitive_level_filter_is_currently_a_no_op():
    """Every exercise in the current database lists every competitive
    level, so this filter shouldn't exclude anything today — see
    ranking.py's module docstring."""
    priorities = [_priority("frontal_knee_control", 1.0)]
    unfiltered = rank_exercises(priorities, age_range="18+", top_n=50)
    filtered = rank_exercises(priorities, age_range="18+", competitive_level="club", top_n=50)
    assert [r.exercise.exercise_id for r in unfiltered] == [r.exercise.exercise_id for r in filtered]


def test_score_sums_severity_across_all_matched_priorities():
    """squat_jump_stick targets landing_control, frontal_knee_control, and
    knee_flexion. Flagging all three should score it higher than flagging
    only one."""
    one_priority = [_priority("knee_flexion", 1.0)]
    three_priorities = [
        _priority("landing_control", 1.0),
        _priority("frontal_knee_control", 1.0),
        _priority("knee_flexion", 1.0),
    ]

    def score_for(exercise_id: str, priorities: list[MovementPriority]) -> float:
        results = rank_exercises(priorities, age_range="18+", top_n=50)
        matches = [r for r in results if r.exercise.exercise_id == exercise_id]
        assert matches, f"{exercise_id} should appear in results"
        return matches[0].score

    assert score_for("squat_jump_stick", three_priorities) > score_for("squat_jump_stick", one_priority)


def test_top_n_limits_result_count():
    # Almost every exercise touches landing_control or frontal_knee_control,
    # so this should easily produce more than 2 eligible matches to trim.
    priorities = [_priority("landing_control", 1.0), _priority("frontal_knee_control", 1.0)]
    results = rank_exercises(priorities, age_range="18+", top_n=2)
    assert len(results) == 2


def test_why_explanation_names_the_flagged_target_and_the_exercise():
    priorities = [_priority("hamstring_strength", 0.8)]
    results = rank_exercises(priorities, age_range="18+")
    assert results
    top = results[0]
    assert "hamstring strength" in top.why
    assert top.exercise.short_description in top.why


def test_results_sorted_by_score_descending():
    priorities = [
        _priority("landing_control", 1.0),
        _priority("frontal_knee_control", 0.5),
        _priority("symmetry", 0.2),
    ]
    results = rank_exercises(priorities, age_range="18+", top_n=20)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
