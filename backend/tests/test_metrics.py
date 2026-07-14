# ============================================================
# test_metrics.py — proves the angle math is correct.
#
# The strategy: feed each function inputs where the answer is
# obvious by hand (an L-shape is 90 deg, a straight line is 180 deg),
# and assert the function returns it. If the math is right on cases
# we KNOW, we can trust it on real landmark data.
#
# Run from the backend/ folder with:  pytest tests/test_metrics.py
# ============================================================

import math
import pytest

from app.cv import metrics


# ---- angle_between: the foundation ----

def test_angle_between_perpendicular():
    # Right (1,0) vs up (0,1) is a 90-degree angle.
    assert metrics.angle_between((1, 0), (0, 1)) == pytest.approx(90.0)


def test_angle_between_same_direction():
    # Two vectors pointing the same way have a 0-degree angle.
    assert metrics.angle_between((2, 0), (5, 0)) == pytest.approx(0.0)


def test_angle_between_opposite_direction():
    # Opposite directions are 180 degrees apart.
    assert metrics.angle_between((1, 0), (-1, 0)) == pytest.approx(180.0)


def test_angle_between_handles_zero_vector():
    # A zero-length vector shouldn't crash; we defined it to return 0.
    assert metrics.angle_between((0, 0), (1, 1)) == 0.0


# ---- angle_at_joint ----

def test_angle_at_joint_right_angle():
    # a above the joint, c to the right of the joint -> 90 degrees.
    a = (0, 0)   # up from b
    b = (0, 1)   # the joint
    c = (1, 1)   # right of b
    assert metrics.angle_at_joint(a, b, c) == pytest.approx(90.0)


def test_angle_at_joint_straight_line():
    # a, b, c collinear -> the joint is "open" at 180 degrees.
    a = (0, 0)
    b = (1, 0)
    c = (2, 0)
    assert metrics.angle_at_joint(a, b, c) == pytest.approx(180.0)


# ---- knee_flexion (0 = straight, larger = more bent) ----

def test_knee_flexion_straight_leg():
    # hip, knee, ankle in a vertical line -> straight leg -> ~0 flexion.
    hip = (0, 0)
    knee = (0, 1)
    ankle = (0, 2)
    assert metrics.knee_flexion(hip, knee, ankle) == pytest.approx(0.0)


def test_knee_flexion_right_angle_bend():
    # A 90-degree bend at the knee -> 90 degrees of flexion.
    hip = (0, 0)     # above the knee
    knee = (0, 1)    # the joint
    ankle = (1, 1)   # ankle juts out to the side
    assert metrics.knee_flexion(hip, knee, ankle) == pytest.approx(90.0)


# ---- hip_flexion ----

def test_hip_flexion_straight_body():
    # shoulder, hip, knee in a line -> standing tall -> ~0 flexion.
    shoulder = (0, 0)
    hip = (0, 1)
    knee = (0, 2)
    assert metrics.hip_flexion(shoulder, hip, knee) == pytest.approx(0.0)


# ---- trunk_lean (0 = upright) ----

def test_trunk_lean_upright():
    # Shoulders directly above hips (smaller y = higher) -> 0 lean.
    hip_mid = (0, 2)
    shoulder_mid = (0, 0)  # straight up from the hips
    assert metrics.trunk_lean(shoulder_mid, hip_mid) == pytest.approx(0.0)


def test_trunk_lean_45_degrees():
    # Shoulders up-and-to-the-right of hips by equal amounts -> 45 deg.
    hip_mid = (0, 0)
    shoulder_mid = (1, -1)  # right 1, up 1
    assert metrics.trunk_lean(shoulder_mid, hip_mid) == pytest.approx(45.0)


# ---- knee_valgus (0 = aligned) ----

def test_knee_valgus_aligned():
    # hip, knee, ankle vertically aligned -> no valgus deviation.
    hip = (0, 0)
    knee = (0, 1)
    ankle = (0, 2)
    assert metrics.knee_valgus(hip, knee, ankle) == pytest.approx(0.0)


# ---- asymmetry_percent ----

def test_asymmetry_identical_sides():
    # Equal left and right values -> 0% asymmetry.
    assert metrics.asymmetry_percent(50.0, 50.0) == pytest.approx(0.0)


def test_asymmetry_known_difference():
    # L=60, R=40: |60-40| / 50 * 100 = 40%.
    assert metrics.asymmetry_percent(60.0, 40.0) == pytest.approx(40.0)
