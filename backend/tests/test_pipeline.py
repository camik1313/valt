# ============================================================
# test_pipeline.py — proves the REAL pipeline (landing detection +
# view-aware branching + baseline correction) produces the correct
# angles end to end, not just that the isolated math in metrics.py is
# right in a vacuum (test_metrics.py already covers that).
#
# STRATEGY: build a synthetic per-frame landmark sequence with a known,
# hand-computed jump-landing shape (standing -> airborne -> landing),
# monkeypatch pose_estimator.extract_landmarks to return it (so this
# doesn't need a real video file or MediaPipe), and run the actual,
# unmodified pipeline.run_pipeline() on it. Everything downstream of
# landmark extraction — landing_detector, find_standing_window, the
# view branch, metrics calls, rounding — runs for real.
#
# Before this file, pipeline.py and landing_detector.py had ZERO direct
# test coverage despite being the app's core scientific logic.
# ============================================================

import pytest

from app.cv import pipeline, pose_estimator

L_SHOULDER, R_SHOULDER = 11, 12
L_HIP, R_HIP = 23, 24
L_KNEE, R_KNEE = 25, 26
L_ANKLE, R_ANKLE = 27, 28

STANDING_FRAMES = 15   # frames 0-14: still, baseline
AIRBORNE_FRAMES = 10   # frames 15-24: hips rise (a jump arc)
LANDING_FRAMES = 25    # frames 25-49: held landing pose (identical each frame)


def _full_frame(overrides: dict[int, tuple[float, float, float, float]]):
    """33 MediaPipe landmarks; unused ones get a harmless placeholder."""
    frame = [(0.5, 0.5, 0.0, 1.0)] * 33
    for i, v in overrides.items():
        frame[i] = v
    return frame


def _build_sequence(standing: dict, landing: dict) -> list:
    """
    standing/landing: {landmark_index: (x, y, z, vis)} for the 8 joints
    we care about, at the standing baseline and at the held landing pose.

    Produces: STANDING_FRAMES of `standing`, then an airborne ramp where
    hip y falls (rises in the image) from the standing hip height toward
    the landing hip height, then LANDING_FRAMES of `landing` held flat —
    a real jump-landing shape for landing_detector to find a peak+trough in.
    """
    frames = []
    for _ in range(STANDING_FRAMES):
        frames.append(_full_frame(standing))

    standing_hip_y = standing[L_HIP][1]
    airborne_peak_y = standing_hip_y - 0.20  # a visible jump into the air
    for i in range(AIRBORNE_FRAMES):
        t = (i + 1) / AIRBORNE_FRAMES
        hip_y = standing_hip_y + t * (airborne_peak_y - standing_hip_y)
        overrides = dict(standing)
        for idx in (L_HIP, R_HIP):
            x, _y, z, v = standing[idx]
            overrides[idx] = (x, hip_y, z, v)
        frames.append(_full_frame(overrides))

    for _ in range(LANDING_FRAMES):
        frames.append(_full_frame(landing))

    return frames


def _run(per_frame, view: str, monkeypatch) -> pipeline.PipelineResult:
    fake_extraction = pose_estimator.PoseExtraction(
        per_frame=per_frame,
        fps=30.0,
        width=1080,
        height=1920,
        frames_read=len(per_frame),
        frames_with_pose=len(per_frame),
    )
    monkeypatch.setattr(pose_estimator, "extract_landmarks", lambda video_path: fake_extraction)
    return pipeline.run_pipeline(seed="synthetic", video_path="unused.mp4", view=view)


# ============================================================
# SIDE VIEW — knee/hip flexion, forward trunk lean.
# No real side-view footage is available locally, so this synthetic
# check is the only end-to-end coverage of the sagittal-plane branch.
# ============================================================

def test_side_view_pipeline_measures_known_flexion_angles(monkeypatch):
    standing = {
        L_SHOULDER: (0.5, 0.25, 0.0, 1.0), R_SHOULDER: (0.5, 0.25, 0.0, 1.0),
        L_HIP: (0.5, 0.55, 0.0, 1.0), R_HIP: (0.5, 0.55, 0.0, 1.0),
        L_KNEE: (0.5, 0.75, 0.0, 1.0), R_KNEE: (0.5, 0.75, 0.0, 1.0),
        L_ANKLE: (0.5, 0.95, 0.0, 1.0), R_ANKLE: (0.5, 0.95, 0.0, 1.0),
    }
    # Knee shifted forward of the hip-ankle line (a real forward knee bend);
    # shoulder forward and up of the hip (a forward trunk lean). Ankle stays
    # planted at the standing x/y — the foot doesn't move during a landing.
    landing = {
        L_SHOULDER: (0.55, 0.30, 0.0, 1.0), R_SHOULDER: (0.55, 0.30, 0.0, 1.0),
        L_HIP: (0.5, 0.55, 0.0, 1.0), R_HIP: (0.5, 0.55, 0.0, 1.0),
        L_KNEE: (0.65, 0.75, 0.0, 1.0), R_KNEE: (0.65, 0.75, 0.0, 1.0),
        L_ANKLE: (0.5, 0.95, 0.0, 1.0), R_ANKLE: (0.5, 0.95, 0.0, 1.0),
    }
    per_frame = _build_sequence(standing, landing)

    result = _run(per_frame, "side", monkeypatch)

    # The detector should land somewhere in the held landing plateau —
    # every frame there has identical, known geometry.
    assert STANDING_FRAMES + AIRBORNE_FRAMES <= result.landing_frame < len(per_frame)

    # Hand-computed from the landing geometry above:
    #   knee vectors: knee->hip = (-0.15,-0.20), knee->ankle = (-0.15, 0.20)
    #   interior angle = arccos(-0.0175 / 0.0625) ~= 106.26 deg -> flexion ~= 73.74 deg
    assert result.measurements["knee_flexion_left"] == pytest.approx(73.7, abs=0.1)
    assert result.measurements["knee_flexion_right"] == pytest.approx(73.7, abs=0.1)
    assert result.measurements["flexion_asymmetry"] == pytest.approx(0.0, abs=0.01)

    #   hip vectors: hip->shoulder = (0.05,-0.25), hip->knee = (0.15,0.20)
    #   interior angle = arccos(-0.0425/0.06375) ~= 131.82 deg -> flexion ~= 48.18 deg
    assert result.measurements["hip_flexion_left"] == pytest.approx(48.2, abs=0.1)

    #   trunk vector (0.05,-0.25) vs vertical (0,-1) -> ~11.31 deg
    assert result.measurements["trunk_lean_forward"] == pytest.approx(11.3, abs=0.1)

    # A front-view-only measurement must NOT appear on a side-view result.
    assert "knee_valgus_left" not in result.measurements


def test_side_view_straight_leg_landing_reads_near_zero_flexion(monkeypatch):
    # A landing pose identical to standing (no bend at all) should read
    # ~0 deg flexion — the "straight leg" sanity case from test_metrics.py,
    # now proven through the real pipeline instead of the bare function.
    pose = {
        L_SHOULDER: (0.5, 0.25, 0.0, 1.0), R_SHOULDER: (0.5, 0.25, 0.0, 1.0),
        L_HIP: (0.5, 0.55, 0.0, 1.0), R_HIP: (0.5, 0.55, 0.0, 1.0),
        L_KNEE: (0.5, 0.75, 0.0, 1.0), R_KNEE: (0.5, 0.75, 0.0, 1.0),
        L_ANKLE: (0.5, 0.95, 0.0, 1.0), R_ANKLE: (0.5, 0.95, 0.0, 1.0),
    }
    per_frame = _build_sequence(pose, pose)

    result = _run(per_frame, "side", monkeypatch)

    assert result.measurements["knee_flexion_left"] == pytest.approx(0.0, abs=0.1)
    assert result.measurements["trunk_lean_forward"] == pytest.approx(0.0, abs=0.1)


# ============================================================
# FRONT VIEW — knee valgus (baseline-corrected), asymmetry, KASR.
# ============================================================

def test_front_view_pipeline_measures_known_valgus_with_baseline_correction(monkeypatch):
    standing = {
        L_SHOULDER: (0.4, 0.25, 0.0, 1.0), R_SHOULDER: (0.6, 0.25, 0.0, 1.0),
        L_HIP: (0.4, 0.50, 0.0, 1.0), R_HIP: (0.6, 0.50, 0.0, 1.0),
        L_KNEE: (0.4, 0.70, 0.0, 1.0), R_KNEE: (0.6, 0.70, 0.0, 1.0),  # tracks straight
        L_ANKLE: (0.4, 0.90, 0.0, 1.0), R_ANKLE: (0.6, 0.90, 0.0, 1.0),
    }
    # Left knee driven 0.04 (of frame width) medially, right knee 0.02
    # medially. Hip width is 0.2, so that's -0.20 HW left, -0.10 HW right
    # (negative = lateral per knee_valgus_index's sign convention — see
    # metrics.py; the SIGN isn't the point here, the exact MAGNITUDE from
    # a known pixel offset is).
    landing = {
        L_SHOULDER: (0.4, 0.25, 0.0, 1.0), R_SHOULDER: (0.6, 0.25, 0.0, 1.0),
        L_HIP: (0.4, 0.50, 0.0, 1.0), R_HIP: (0.6, 0.50, 0.0, 1.0),
        L_KNEE: (0.44, 0.70, 0.0, 1.0), R_KNEE: (0.58, 0.70, 0.0, 1.0),
        L_ANKLE: (0.4, 0.90, 0.0, 1.0), R_ANKLE: (0.6, 0.90, 0.0, 1.0),
    }
    per_frame = _build_sequence(standing, landing)

    result = _run(per_frame, "front", monkeypatch)

    assert STANDING_FRAMES + AIRBORNE_FRAMES <= result.landing_frame < len(per_frame)
    assert any("Standing baseline found" in n for n in result.notes)

    assert result.measurements["knee_valgus_left"] == pytest.approx(-0.20, abs=0.001)
    assert result.measurements["knee_valgus_right"] == pytest.approx(-0.10, abs=0.001)
    # asymmetry_percent(-0.20, -0.10) = |(-0.20)-(-0.10)| / mean(0.20,0.10) * 100
    assert result.measurements["valgus_asymmetry"] == pytest.approx(66.7, abs=0.1)

    # A side-view-only measurement must NOT appear on a front-view result.
    assert "knee_flexion_left" not in result.measurements


def test_front_view_symmetric_landing_reads_zero_valgus_and_asymmetry(monkeypatch):
    pose = {
        L_SHOULDER: (0.4, 0.25, 0.0, 1.0), R_SHOULDER: (0.6, 0.25, 0.0, 1.0),
        L_HIP: (0.4, 0.50, 0.0, 1.0), R_HIP: (0.6, 0.50, 0.0, 1.0),
        L_KNEE: (0.4, 0.70, 0.0, 1.0), R_KNEE: (0.6, 0.70, 0.0, 1.0),
        L_ANKLE: (0.4, 0.90, 0.0, 1.0), R_ANKLE: (0.6, 0.90, 0.0, 1.0),
    }
    per_frame = _build_sequence(pose, pose)

    result = _run(per_frame, "front", monkeypatch)

    assert result.measurements["knee_valgus_left"] == pytest.approx(0.0, abs=0.001)
    assert result.measurements["knee_valgus_right"] == pytest.approx(0.0, abs=0.001)
    assert result.measurements["valgus_asymmetry"] == pytest.approx(0.0, abs=0.01)
