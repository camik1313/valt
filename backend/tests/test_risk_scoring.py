# ============================================================
# test_risk_scoring.py — proves the screening score math is correct
# and, just as importantly, that it never claims to be more than a
# screening score (see risk/scoring.py's module docstring).
#
# Strategy: feed known measurement/questionnaire values chosen relative
# to the exact thresholds in risk/scoring.py, and assert the expected
# points, percent, and band come out. Boundary cases (value == threshold)
# get their own tests since "ge" vs "lt" behave differently there.
# ============================================================

import pytest

from app.risk import scoring
from app.risk.scoring import QuestionnaireAnswers


# ---- score_biomechanics: empty / no signal ----

def test_biomechanics_empty_measurements():
    result = scoring.score_biomechanics({})
    assert result.points == 0.0
    assert result.max_points == 0.0
    assert result.factors == []


def test_biomechanics_ignores_unrelated_keys():
    # kasr isn't a scored criterion; mock-pipeline generic keys aren't either.
    result = scoring.score_biomechanics({"kasr": 0.5, "knee_flexion": 80.0})
    assert result.points == 0.0
    assert result.max_points == 0.0


# ---- score_biomechanics: front-view (frontal plane) criteria ----

def test_biomechanics_front_view_all_triggered():
    measurements = {
        "knee_valgus_left": 0.20,     # >= 0.15 threshold
        "knee_valgus_right": -0.22,   # abs(-0.22) >= 0.15
        "valgus_asymmetry": 30.0,     # >= 25.0 threshold
        "trunk_lean_lateral": 12.0,   # >= 10.0 threshold
    }
    result = scoring.score_biomechanics(measurements)
    assert result.max_points == pytest.approx(7.0)   # 2 + 2 + 1.5 + 1.5
    assert result.points == pytest.approx(7.0)
    assert len(result.factors) == 4


def test_biomechanics_front_view_none_triggered():
    measurements = {
        "knee_valgus_left": 0.10,     # < 0.15
        "knee_valgus_right": 0.05,    # < 0.15
        "valgus_asymmetry": 10.0,     # < 25.0
        "trunk_lean_lateral": 5.0,    # < 10.0
    }
    result = scoring.score_biomechanics(measurements)
    assert result.max_points == pytest.approx(7.0)
    assert result.points == pytest.approx(0.0)
    assert result.factors == []


def test_biomechanics_valgus_threshold_is_inclusive():
    # direction="abs_ge": value exactly at threshold DOES trigger.
    result = scoring.score_biomechanics({"knee_valgus_left": 0.15})
    assert result.points == pytest.approx(2.0)


# ---- score_biomechanics: side-view (sagittal plane) criteria ----

def test_biomechanics_flexion_threshold_is_exclusive():
    # direction="lt": value exactly at threshold does NOT trigger.
    result = scoring.score_biomechanics({"knee_flexion_left": 55.0})
    assert result.points == pytest.approx(0.0)
    assert result.max_points == pytest.approx(2.0)

    result_below = scoring.score_biomechanics({"knee_flexion_left": 54.9})
    assert result_below.points == pytest.approx(2.0)


def test_biomechanics_side_view_moderate_mix():
    measurements = {
        "knee_flexion_left": 40.0,    # < 55 -> triggers (+2)
        "knee_flexion_right": 70.0,   # not triggered
        "flexion_asymmetry": 5.0,     # < 15 -> not triggered
        "trunk_lean_forward": 15.0,   # < 20 -> triggers (+2)
    }
    result = scoring.score_biomechanics(measurements)
    assert result.max_points == pytest.approx(7.5)   # 2 + 2 + 1.5 + 2
    assert result.points == pytest.approx(4.0)
    assert {f.key for f in result.factors} == {
        "knee_flexion_left", "trunk_forward_flexion_deficit",
    }


# ---- score_questionnaire ----

def test_questionnaire_none_returns_none():
    assert scoring.score_questionnaire(None) is None


def test_questionnaire_all_fields_unanswered_scores_zero():
    result = scoring.score_questionnaire(QuestionnaireAnswers())
    assert result.points == 0.0
    assert result.max_points == 0.0
    assert result.factors == []


def test_questionnaire_all_max_risk_answers():
    answers = QuestionnaireAnswers(
        previous_acl_injury=True,
        sex="female",
        sport_type="pivoting_cutting",
        age=18,
        activity_level="competitive_high_school",
        fatigue_reported=True,
        previous_lower_limb_injury=True,
    )
    result = scoring.score_questionnaire(answers)
    assert result.max_points == pytest.approx(12.5)   # 4+2+2+1+1.5+1+1
    assert result.points == pytest.approx(12.5)
    assert len(result.factors) == 7


def test_questionnaire_answered_but_negative_still_counts_toward_max():
    # Answering "no" to a question still makes it an ASKED question, so it
    # should count toward max_points (the achievable total) even though it
    # contributes 0 points. Otherwise percent-of-max would be gamed by
    # answering "no" to reduce the denominator.
    answers = QuestionnaireAnswers(previous_acl_injury=False, sex="male")
    result = scoring.score_questionnaire(answers)
    assert result.max_points == pytest.approx(6.0)   # 4 (asked) + 2 (asked)
    assert result.points == pytest.approx(0.0)
    assert result.factors == []


def test_questionnaire_sport_type_max_is_the_riskiest_category_not_the_answer():
    # Someone reporting a low-risk sport should still be measured against
    # the max ACHIEVABLE sport-type points (pivoting_cutting = 2.0), not
    # against their own category's ceiling.
    answers = QuestionnaireAnswers(sport_type="endurance_noncontact")
    result = scoring.score_questionnaire(answers)
    assert result.max_points == pytest.approx(2.0)
    assert result.points == pytest.approx(0.0)


def test_questionnaire_age_outside_high_incidence_range():
    result = scoring.score_questionnaire(QuestionnaireAnswers(age=45))
    assert result.max_points == pytest.approx(1.0)
    assert result.points == pytest.approx(0.0)


def test_questionnaire_age_inside_high_incidence_range():
    result = scoring.score_questionnaire(QuestionnaireAnswers(age=16))
    assert result.points == pytest.approx(1.0)


# ---- compute_screening_score: combined bands ----

def test_screening_score_no_signal_is_low_band():
    result = scoring.compute_screening_score({})
    assert result.band == "low"
    assert result.percent_of_max == 0.0
    assert result.questionnaire is None
    assert result.factors == []


def test_screening_score_biomechanics_only_elevated_band():
    measurements = {
        "knee_valgus_left": 0.30,
        "knee_valgus_right": 0.30,
        "valgus_asymmetry": 40.0,
        "trunk_lean_lateral": 15.0,
    }
    result = scoring.compute_screening_score(measurements)
    assert result.band == "elevated"
    assert result.percent_of_max == pytest.approx(100.0)
    assert result.questionnaire is None
    assert len(result.factors) == 4


def test_screening_score_moderate_band():
    measurements = {
        "knee_flexion_left": 40.0,    # triggers, +2 of 7.5 max
        "knee_flexion_right": 70.0,
        "flexion_asymmetry": 5.0,
        "trunk_lean_forward": 15.0,   # triggers, +2 of 7.5 max
    }
    result = scoring.compute_screening_score(measurements)
    # 4.0 / 7.5 = 53.3% -> moderate band (34 <= x < 67)
    assert result.percent_of_max == pytest.approx(53.3, abs=0.1)
    assert result.band == "moderate"


def test_screening_score_combines_biomechanics_and_questionnaire():
    measurements = {"knee_valgus_left": 0.20}   # +2 of 2 max
    answers = QuestionnaireAnswers(previous_acl_injury=True)  # +4 of 4 max
    result = scoring.compute_screening_score(measurements, answers)
    assert result.total_points == pytest.approx(6.0)
    assert result.total_max_points == pytest.approx(6.0)
    assert result.band == "elevated"
    assert result.questionnaire is not None
    assert result.questionnaire.points == pytest.approx(4.0)
    assert result.biomechanical.points == pytest.approx(2.0)
    assert len(result.factors) == 2


def test_screening_score_never_reports_a_probability_field():
    # Guardrail: the result object must not expose anything that looks
    # like an injury probability/likelihood. Only points/percent/band.
    result = scoring.compute_screening_score({"knee_valgus_left": 0.20})
    field_names = set(vars(result).keys())
    for banned in ("probability", "likelihood", "risk_percent", "chance"):
        assert banned not in field_names
    assert result.disclaimer  # always present and non-empty
    assert "not a diagnosis" in result.disclaimer.lower()
