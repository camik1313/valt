# ============================================================
# test_less.py — proves the real 17-item LESS scoring engine
# (app/risk/less.py) computes each item correctly from known raw
# inputs, and that the questionnaire items (13, 14, 17) integrate
# cleanly with the auto-measured ones.
# ============================================================

import pytest

from app.risk import less


# ---- Empty input ----

def test_no_raw_measurements_scores_nothing():
    result = less.compute_less_score({})
    assert result.total_points == 0
    assert result.max_points == 0
    assert result.items == []
    assert result.views_available == []
    assert result.band == "low"


# ---- Sagittal items (1-7) ----

def test_sagittal_all_errors():
    raw = {
        "less_knee_flexion_ic_left": 20.0,          # <=30 -> error (item 1)
        "less_hip_flexion_ic_left": 5.0,             # <=10 -> error (item 2)
        "less_trunk_flexion_ic": 3.0,                # <=10 -> error (item 3)
        "less_knee_flexion_displacement_left": 30.0,  # <=45 -> error (item 4)
        "less_hip_flexion_displacement_left": 2.0,   # <=5 -> error (item 5)
        "less_trunk_flexion_displacement": 1.0,      # <=5 -> error (item 6)
        "less_toe_to_heel_offset_left": 0.0,         # <=0.01 -> error (item 7)
    }
    result = less.compute_less_score(raw)
    assert result.views_available == ["side"]
    # Items 1-7 (sagittal), PLUS item 16 — the displacement proxy always
    # piggybacks whenever any displacement value is present (it is here,
    # via items 4-6's raw values). Its band: 30+2+1=33 deg total < 50 ->
    # "stiff" -> 2 pts.
    assert len(result.items) == 8
    assert result.max_points == 7 + 2
    assert result.total_points == 7 + 2
    item16 = next(i for i in result.items if i.number == 16)
    assert item16.points == 2
    assert all(item.source == "measured" for item in result.items)


def test_sagittal_all_pass():
    raw = {
        "less_knee_flexion_ic_left": 40.0,           # >30 -> no error
        "less_hip_flexion_ic_left": 25.0,            # >10 -> no error
        "less_trunk_flexion_ic": 20.0,               # >10 -> no error
        "less_knee_flexion_displacement_left": 60.0,  # >45 -> no error
        "less_hip_flexion_displacement_left": 15.0,  # >5 -> no error
        "less_trunk_flexion_displacement": 10.0,     # >5 -> no error
        "less_toe_to_heel_offset_left": 0.05,        # >0.01 -> no error
    }
    result = less.compute_less_score(raw)
    # Same piggyback as above: item 16's total is 60+15+10=85, between 50
    # and 90 -> "average" -> 1 pt (not 0 — a soft landing needs >=90).
    assert result.max_points == 7 + 2
    item16 = next(i for i in result.items if i.number == 16)
    assert item16.points == 1
    assert result.total_points == 1


def test_sagittal_uses_worse_leg():
    # Left leg passes item 1's threshold, right leg fails it -> the
    # official form scores ONE checkbox per trial, so the worse leg wins.
    raw = {
        "less_knee_flexion_ic_left": 50.0,   # fine
        "less_knee_flexion_ic_right": 10.0,  # <=30 -> error
    }
    result = less.compute_less_score(raw)
    item1 = next(i for i in result.items if i.number == 1)
    assert item1.points == 1


# ---- Frontal items (8, 9, 10, 11/12, 15) ----

def test_frontal_all_errors():
    raw = {
        "less_foot_contact_asymmetry_frames": 5.0,   # >2 -> error (item 8)
        "less_trunk_lateral_ic": 15.0,                # >=10 -> error (item 9)
        "less_knee_valgus_ic_left": -0.20,            # |..|>=0.15 -> error (item 10)
        "less_stance_width_ratio_ic": 0.7,            # <1 -> narrow error (item 11), not wide (item 12)
        "less_knee_valgus_displacement_left": 0.15,   # >=0.10 -> error (item 15)
    }
    result = less.compute_less_score(raw)
    assert result.views_available == ["front"]
    by_number = {i.number: i for i in result.items}
    assert by_number[8].points == 1
    assert by_number[9].points == 1
    assert by_number[10].points == 1
    assert by_number[11].points == 1   # narrow
    assert by_number[12].points == 0   # not wide
    assert by_number[15].points == 1
    assert result.max_points == 6   # items 8,9,10,11,12,15
    assert result.total_points == 5


def test_stance_width_wide_triggers_only_item_12():
    raw = {"less_stance_width_ratio_ic": 1.3}
    result = less.compute_less_score(raw)
    by_number = {i.number: i for i in result.items}
    assert by_number[11].points == 0
    assert by_number[12].points == 1


def test_frontal_all_pass():
    raw = {
        "less_foot_contact_asymmetry_frames": 0.0,
        "less_trunk_lateral_ic": 2.0,
        "less_knee_valgus_ic_left": 0.02,
        "less_stance_width_ratio_ic": 1.0,
        "less_knee_valgus_displacement_left": 0.01,
    }
    result = less.compute_less_score(raw)
    assert result.total_points == 0
    assert result.max_points == 6


# ---- Item 16 (joint displacement proxy) ----

def test_displacement_proxy_soft():
    raw = {
        "less_knee_flexion_displacement_left": 50.0,
        "less_hip_flexion_displacement_left": 30.0,
        "less_trunk_flexion_displacement": 20.0,   # total 100 >= 90 -> soft -> 0 pts
    }
    result = less.compute_less_score(raw)
    item16 = next(i for i in result.items if i.number == 16)
    assert item16.points == 0
    assert item16.max_points == 2


def test_displacement_proxy_stiff():
    raw = {
        "less_knee_flexion_displacement_left": 10.0,
        "less_hip_flexion_displacement_left": 5.0,
        "less_trunk_flexion_displacement": 5.0,   # total 20 < 50 -> stiff -> 2 pts
    }
    result = less.compute_less_score(raw)
    item16 = next(i for i in result.items if i.number == 16)
    assert item16.points == 2


def test_displacement_proxy_average():
    raw = {
        "less_knee_flexion_displacement_left": 40.0,
        "less_hip_flexion_displacement_left": 20.0,
        "less_trunk_flexion_displacement": 10.0,   # total 70, between 50 and 90 -> average -> 1 pt
    }
    result = less.compute_less_score(raw)
    item16 = next(i for i in result.items if i.number == 16)
    assert item16.points == 1


# ---- Questionnaire items (13, 14, 17) ----

def test_questionnaire_none_contributes_nothing():
    result = less.compute_less_score({}, None)
    assert not any(i.number in (13, 14, 17) for i in result.items)


def test_questionnaire_all_answered_worst_case():
    answers = less.LessQuestionnaireAnswers(
        foot_ir_max_flexion=True,
        foot_er_max_flexion=True,
        overall_impression="poor",
    )
    result = less.compute_less_score({}, answers)
    by_number = {i.number: i for i in result.items}
    assert by_number[13].points == 1
    assert by_number[14].points == 1
    assert by_number[17].points == 2
    assert by_number[17].max_points == 2
    assert result.max_points == 4  # 1+1+2
    assert result.total_points == 4
    assert all(i.source == "self_reported" for i in result.items)


def test_questionnaire_excellent_overall_scores_zero():
    answers = less.LessQuestionnaireAnswers(overall_impression="excellent")
    result = less.compute_less_score({}, answers)
    item17 = next(i for i in result.items if i.number == 17)
    assert item17.points == 0


# ---- Combined front + side + questionnaire ----

def test_combined_session_widens_max_points_and_bands_correctly():
    raw = {
        # sagittal (7 items, all pass)
        "less_knee_flexion_ic_left": 40.0,
        "less_hip_flexion_ic_left": 25.0,
        "less_trunk_flexion_ic": 20.0,
        "less_knee_flexion_displacement_left": 60.0,
        "less_hip_flexion_displacement_left": 15.0,
        "less_trunk_flexion_displacement": 10.0,
        "less_toe_to_heel_offset_left": 0.05,
        # frontal: items 8, 9, 10, 15 fail; item 11 (narrow) fails since
        # ratio 0.7 < 1; item 12 (wide) does NOT (ratio isn't > 1) — 5 of
        # the 6 frontal items fail, matching test_frontal_all_errors above.
        "less_foot_contact_asymmetry_frames": 5.0,
        "less_trunk_lateral_ic": 15.0,
        "less_knee_valgus_ic_left": -0.20,
        "less_stance_width_ratio_ic": 0.7,
        "less_knee_valgus_displacement_left": 0.15,
    }
    answers = less.LessQuestionnaireAnswers(overall_impression="average")
    result = less.compute_less_score(raw, answers)

    assert sorted(result.views_available) == ["front", "side"]
    # 7 sagittal + 6 frontal + 1 displacement proxy + 1 overall = 15 items
    assert len(result.items) == 15
    # max points: 7 + 6 + 2 (item16) + 2 (item17) = 17
    assert result.max_points == 17

    item16 = next(i for i in result.items if i.number == 16)
    # total displacement = 60+15+10 = 85 -> between 50 and 90 -> "average" -> 1 pt
    assert item16.points == 1

    item17 = next(i for i in result.items if i.number == 17)
    assert item17.points == 1  # "average" overall impression

    # sagittal items all pass (0) + frontal 5 errors (5) + item16 (1) + item17 (1)
    assert result.total_points == 7
    assert result.band == "moderate"  # 5 <= 7 < 9


def test_max_less_score_is_19():
    assert less.MAX_LESS_SCORE == 19


def test_band_thresholds_match_padua_2015_cutoff():
    assert less.band_for_score(4) == "low"
    assert less.band_for_score(5) == "moderate"
    assert less.band_for_score(8) == "moderate"
    assert less.band_for_score(9) == "high"
