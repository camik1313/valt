# ============================================================
# test_priorities.py — the movement-priority detector. Uses hand-built
# LessItemScore fixtures (same technique test_less.py uses) rather than
# a real analysis, so each case isolates exactly one behavior.
# ============================================================

from app.exercises.priorities import detect_priorities
from app.risk.less import LessItemScore


def _less_item(key: str, points: int, max_points: int = 1, label: str | None = None) -> LessItemScore:
    return LessItemScore(
        number=1, key=key, view="frontal", label=label or key,
        good_criterion="n/a", points=points, max_points=max_points,
        source="measured", detail="n/a",
    )


def test_no_priorities_when_nothing_flagged():
    less_items = [_less_item("knee_valgus_ic", points=0), _less_item("trunk_flexion_ic", points=0)]
    metric_status = {"knee_valgus_left": "ok", "trunk_lean_forward": "ok"}
    assert detect_priorities(less_items, metric_status) == []


def test_less_flagged_item_produces_priority():
    less_items = [_less_item("knee_valgus_ic", points=1, max_points=1, label="Knee valgus at initial contact")]
    priorities = detect_priorities(less_items, metric_status={})
    assert len(priorities) == 1
    assert priorities[0].target == "frontal_knee_control"
    assert priorities[0].severity == 1.0
    assert "Knee valgus at initial contact" in priorities[0].evidence[0]


def test_metric_flag_produces_priority_when_less_silent():
    priorities = detect_priorities(less_items=[], metric_status={"trunk_lean_forward": "flag"})
    assert len(priorities) == 1
    assert priorities[0].target == "trunk_control"
    assert priorities[0].severity == 1.0


def test_metric_watch_status_scores_lower_than_flag():
    priorities = detect_priorities(less_items=[], metric_status={"trunk_lean_forward": "watch"})
    assert priorities[0].severity == 0.5


def test_ok_status_never_produces_a_priority():
    priorities = detect_priorities(less_items=[], metric_status={"trunk_lean_forward": "ok"})
    assert priorities == []


def test_takes_the_stronger_signal_not_an_average():
    """A fully-flagged LESS item (fraction 1.0) and a merely-'watch'
    metric (0.5) map to the same target here; the result should be 1.0,
    not a diluted average like 0.75."""
    less_items = [_less_item("knee_valgus_ic", points=1, max_points=1)]
    metric_status = {"knee_valgus_left": "watch"}
    priorities = detect_priorities(less_items, metric_status)
    assert len(priorities) == 1
    assert priorities[0].target == "frontal_knee_control"
    assert priorities[0].severity == 1.0


def test_respects_max_priorities_and_sorts_by_severity_descending():
    less_items = [
        _less_item("knee_valgus_ic", points=1, max_points=1),      # frontal_knee_control, 1.0
        _less_item("trunk_flexion_ic", points=1, max_points=2),    # trunk_control, 0.5
        _less_item("foot_contact_symmetry", points=1, max_points=1),  # symmetry, 1.0
        _less_item("knee_flexion_ic", points=1, max_points=2),     # knee_flexion, 0.5
    ]
    priorities = detect_priorities(less_items, metric_status={}, max_priorities=3)
    assert len(priorities) == 3
    severities = [p.severity for p in priorities]
    assert severities == sorted(severities, reverse=True)
    # The two 1.0-severity targets must both make the cut over the two 0.5s.
    top_targets = {p.target for p in priorities[:2]}
    assert top_targets == {"frontal_knee_control", "symmetry"}


def test_unmapped_less_key_is_ignored_not_erroring():
    less_items = [_less_item("some_future_item_key", points=1, max_points=1)]
    assert detect_priorities(less_items, metric_status={}) == []
