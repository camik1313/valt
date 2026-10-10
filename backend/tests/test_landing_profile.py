# ============================================================
# test_landing_profile.py — the always-4-categories summary. Uses
# hand-built Metric/LessItemScore fixtures, same technique
# test_priorities.py uses, so each case isolates one behavior.
# ============================================================

import dataclasses

from app.models.schemas import Metric
from app.reports.landing_profile import compute_landing_profile
from app.risk.less import LessItemScore


def _metric(key: str, value: float, status: str, unit: str = "deg") -> Metric:
    return Metric(key=key, label=key.replace("_", " ").title(), value=value, unit=unit, status=status)


def _less_item(key: str, points: int, max_points: int = 1) -> LessItemScore:
    return LessItemScore(
        number=1, key=key, view="frontal", label=key, good_criterion="n/a",
        points=points, max_points=max_points, source="measured", detail="n/a",
    )


def test_always_returns_exactly_four_categories():
    profile = compute_landing_profile(metrics_list=[], less_items=[])
    assert len(profile.categories) == 4
    assert {c.category for c in profile.categories} == {
        "knee_control", "landing_depth", "symmetry", "trunk_control",
    }


def test_unavailable_when_nothing_measured_for_a_category():
    profile = compute_landing_profile(metrics_list=[], less_items=[])
    knee_control = next(c for c in profile.categories if c.category == "knee_control")
    assert knee_control.rating == "unavailable"
    assert knee_control.value is None


def test_ok_rating_from_a_clean_metric():
    metrics = [_metric("trunk_lean_lateral", 3.0, "ok")]
    profile = compute_landing_profile(metrics_list=metrics, less_items=[])
    trunk = next(c for c in profile.categories if c.category == "trunk_control")
    assert trunk.rating == "ok"
    assert trunk.value == 3.0
    assert trunk.source_view == "front"


def test_flagged_metric_produces_flag_rating():
    metrics = [_metric("knee_valgus_left", 0.3, "flag", unit="HW")]
    profile = compute_landing_profile(metrics_list=metrics, less_items=[])
    knee = next(c for c in profile.categories if c.category == "knee_control")
    assert knee.rating == "flag"
    assert "inward" in knee.explanation


def test_flagged_less_item_overrides_an_ok_metric():
    """A validated LESS flag should win even if the raw metric alone
    would only read as 'ok' — the clinical item is the stronger signal."""
    metrics = [_metric("knee_valgus_left", 0.05, "ok", unit="HW")]
    less_items = [_less_item("knee_valgus_ic", points=1, max_points=1)]
    profile = compute_landing_profile(metrics_list=metrics, less_items=less_items)
    knee = next(c for c in profile.categories if c.category == "knee_control")
    assert knee.rating == "flag"


def test_watch_status_produces_watch_rating():
    metrics = [_metric("flexion_asymmetry", 12.0, "watch", unit="%")]
    profile = compute_landing_profile(metrics_list=metrics, less_items=[])
    symmetry = next(c for c in profile.categories if c.category == "symmetry")
    assert symmetry.rating == "watch"


def test_worse_of_two_candidates_is_selected_as_representative():
    metrics = [
        _metric("knee_valgus_left", 0.05, "ok", unit="HW"),
        _metric("knee_valgus_right", 0.30, "flag", unit="HW"),
    ]
    profile = compute_landing_profile(metrics_list=metrics, less_items=[])
    knee = next(c for c in profile.categories if c.category == "knee_control")
    assert knee.value == 0.30
    assert knee.rating == "flag"


def test_side_view_metric_reports_side_source():
    metrics = [_metric("knee_flexion_left", 40.0, "ok")]
    profile = compute_landing_profile(metrics_list=metrics, less_items=[])
    depth = next(c for c in profile.categories if c.category == "landing_depth")
    assert depth.source_view == "side"


def test_outward_knee_motion_is_not_described_as_inward():
    # Negative valgus index = knee outward of the hip-ankle line. It is
    # banded on magnitude, so the wording must follow the sign.
    for status, word in (("flag", "outward"), ("watch", "outward")):
        profile = compute_landing_profile([_metric("knee_valgus_left", -0.4, status, "HW")], [])
        knee = next(c for c in profile.categories if c.category == "knee_control")
        assert word in knee.explanation
        assert "inward" not in knee.explanation


def test_inward_knee_motion_still_described_as_inward():
    profile = compute_landing_profile([_metric("knee_valgus_left", 0.4, "flag", "HW")], [])
    knee = next(c for c in profile.categories if c.category == "knee_control")
    assert "inward" in knee.explanation


def test_less_driven_flag_does_not_claim_a_stiff_landing_next_to_a_deep_knee_bend():
    # Regression from a real run: knee flexion 104 deg (status ok) but LESS
    # displacement items flagged, so the generic "stiff landing, limited knee
    # bend" sentence contradicted the number shown right beside it.
    less = [_less_item("knee_flexion_displacement", points=1)]
    less[0] = dataclasses.replace(less[0], label="Knee flexion displacement")
    profile = compute_landing_profile([_metric("knee_flexion_left", 104.3, "ok")], less)

    depth = next(c for c in profile.categories if c.category == "landing_depth")
    assert depth.rating == "flag"
    assert "stiff" not in depth.explanation
    assert "limited knee bend" not in depth.explanation
    assert "LESS" in depth.explanation
    assert "knee flexion displacement" in depth.explanation
    assert "uncertain" in depth.explanation


def test_metric_driven_flag_keeps_the_plain_category_sentence():
    profile = compute_landing_profile([_metric("knee_flexion_left", 30.0, "flag")], [])
    depth = next(c for c in profile.categories if c.category == "landing_depth")
    assert "stiff" in depth.explanation


def test_upright_trunk_is_not_described_as_leaning():
    profile = compute_landing_profile([_metric("trunk_lean_forward", 6.0, "watch")], [])
    trunk = next(c for c in profile.categories if c.category == "trunk_control")
    assert trunk.rating == "watch"
    assert "upright" in trunk.explanation
    assert "leaned" not in trunk.explanation
