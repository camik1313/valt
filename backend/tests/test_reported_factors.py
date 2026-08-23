# ============================================================
# test_reported_factors.py — proves risk/reported_factors.py builds the
# right unscored factor list from a self-report questionnaire: only
# literature-associated answers produce a factor, unanswered/non-matching
# fields don't, and every factor carries a citation.
# ============================================================

from app.risk.reported_factors import QuestionnaireAnswers, reported_risk_factors


def test_no_answers_produces_no_factors():
    assert reported_risk_factors(None) == []
    assert reported_risk_factors(QuestionnaireAnswers()) == []


def test_previous_acl_injury_produces_a_factor():
    factors = reported_risk_factors(QuestionnaireAnswers(previous_acl_injury=True))
    assert [f.key for f in factors] == ["previous_acl_injury"]
    assert factors[0].citation


def test_previous_acl_injury_false_produces_no_factor():
    factors = reported_risk_factors(QuestionnaireAnswers(previous_acl_injury=False))
    assert factors == []


def test_female_sex_produces_a_factor_other_sexes_do_not():
    assert [f.key for f in reported_risk_factors(QuestionnaireAnswers(sex="female"))] == ["sex"]
    assert reported_risk_factors(QuestionnaireAnswers(sex="male")) == []


def test_pivoting_and_field_court_sports_produce_a_factor_endurance_does_not():
    assert [f.key for f in reported_risk_factors(QuestionnaireAnswers(sport_type="pivoting_cutting"))] == ["sport_type"]
    assert [f.key for f in reported_risk_factors(QuestionnaireAnswers(sport_type="field_court_other"))] == ["sport_type"]
    assert reported_risk_factors(QuestionnaireAnswers(sport_type="endurance_noncontact")) == []


def test_age_in_range_produces_a_factor_outside_range_does_not():
    assert [f.key for f in reported_risk_factors(QuestionnaireAnswers(age=16))] == ["age"]
    assert reported_risk_factors(QuestionnaireAnswers(age=8)) == []
    assert reported_risk_factors(QuestionnaireAnswers(age=40)) == []


def test_competitive_activity_levels_produce_a_factor_others_do_not():
    assert [f.key for f in reported_risk_factors(QuestionnaireAnswers(activity_level="competitive_high_school"))] == ["activity_level"]
    assert reported_risk_factors(QuestionnaireAnswers(activity_level="recreational")) == []


def test_fatigue_and_previous_lower_limb_injury_produce_factors():
    assert [f.key for f in reported_risk_factors(QuestionnaireAnswers(fatigue_reported=True))] == ["fatigue_reported"]
    assert [f.key for f in reported_risk_factors(QuestionnaireAnswers(previous_lower_limb_injury=True))] == ["previous_lower_limb_injury"]


def test_multiple_matching_answers_all_produce_factors():
    answers = QuestionnaireAnswers(
        previous_acl_injury=True,
        sex="female",
        sport_type="pivoting_cutting",
        age=16,
        activity_level="competitive_high_school",
        fatigue_reported=True,
        previous_lower_limb_injury=True,
    )
    keys = {f.key for f in reported_risk_factors(answers)}
    assert keys == {
        "previous_acl_injury", "sex", "sport_type", "age",
        "activity_level", "fatigue_reported", "previous_lower_limb_injury",
    }
