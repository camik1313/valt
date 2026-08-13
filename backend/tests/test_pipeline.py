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


def test_front_view_asymmetry_uses_baseline_corrected_values(monkeypatch):
    # Regression test: valgus_asymmetry must be computed from the SAME
    # baseline-corrected numbers reported as knee_valgus_left/right, not
    # the raw pre-correction landing-frame values. The case above has a
    # zero standing offset for both legs, so raw and corrected happen to
    # be identical there and can't tell the two implementations apart.
    # Here the standing pose already has a nonzero left-knee offset, so
    # the two computations diverge (100% from raw vs 66.7% from corrected)
    # and only the corrected one should come out.
    standing = {
        L_SHOULDER: (0.4, 0.25, 0.0, 1.0), R_SHOULDER: (0.6, 0.25, 0.0, 1.0),
        L_HIP: (0.4, 0.50, 0.0, 1.0), R_HIP: (0.6, 0.50, 0.0, 1.0),
        L_KNEE: (0.42, 0.70, 0.0, 1.0), R_KNEE: (0.6, 0.70, 0.0, 1.0),
        L_ANKLE: (0.4, 0.90, 0.0, 1.0), R_ANKLE: (0.6, 0.90, 0.0, 1.0),
    }
    landing = {
        L_SHOULDER: (0.4, 0.25, 0.0, 1.0), R_SHOULDER: (0.6, 0.25, 0.0, 1.0),
        L_HIP: (0.4, 0.50, 0.0, 1.0), R_HIP: (0.6, 0.50, 0.0, 1.0),
        L_KNEE: (0.46, 0.70, 0.0, 1.0), R_KNEE: (0.58, 0.70, 0.0, 1.0),
        L_ANKLE: (0.4, 0.90, 0.0, 1.0), R_ANKLE: (0.6, 0.90, 0.0, 1.0),
    }
    per_frame = _build_sequence(standing, landing)

    result = _run(per_frame, "front", monkeypatch)

    # Baseline-corrected: left -0.30 - (-0.10) = -0.20, right -0.10 - 0 = -0.10.
    assert result.measurements["knee_valgus_left"] == pytest.approx(-0.20, abs=0.001)
    assert result.measurements["knee_valgus_right"] == pytest.approx(-0.10, abs=0.001)
    # Must match asymmetry_percent(-0.20, -0.10) = 66.7%, reproducible by
    # hand from the two values above — NOT the raw-value answer (100%).
    assert result.measurements["valgus_asymmetry"] == pytest.approx(66.7, abs=0.1)


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


# ============================================================
# LESS (Landing Error Scoring System) raw measurements.
#
# _build_sequence() above can't test the initial-contact-vs-max-flexion
# split: it transitions every landmark at the same single frame boundary,
# so ankle and hip always "settle" together. Real landings don't work
# that way — the feet stop descending (touch down) before the hip
# finishes flexing into the squat — so this test uses a bespoke sequence
# where the ankle plants and goes flat several frames before the hip
# does, and checks that initial_contact_frame lands meaningfully earlier
# than landing_frame (max flexion) as a result.
# ============================================================

def _less_test_frame(hip_y: float, ankle_y: float, knee_offset_x: float = 0.0):
    return {
        L_SHOULDER: (0.5, 0.25, 0.0, 1.0), R_SHOULDER: (0.5, 0.25, 0.0, 1.0),
        L_HIP: (0.5, hip_y, 0.0, 1.0), R_HIP: (0.5, hip_y, 0.0, 1.0),
        L_KNEE: (0.5 + knee_offset_x, 0.70, 0.0, 1.0), R_KNEE: (0.5 + knee_offset_x, 0.70, 0.0, 1.0),
        L_ANKLE: (0.5, ankle_y, 0.0, 1.0), R_ANKLE: (0.5, ankle_y, 0.0, 1.0),
    }


def test_initial_contact_detected_before_max_flexion_when_separable(monkeypatch):
    frames = []
    # Standing (10 frames): hip=0.50, ankle=0.90, straight leg.
    for _ in range(10):
        frames.append(_full_frame(_less_test_frame(0.50, 0.90)))
    # Airborne (10 frames): hip and ankle rise together (0.50->0.30, 0.90->0.75).
    for i in range(10):
        t = (i + 1) / 10
        frames.append(_full_frame(_less_test_frame(0.50 - t * 0.20, 0.90 - t * 0.15)))
    # Feet land (ankle flat at 0.90) while the hip KEEPS descending for 10
    # more frames (0.30 -> 0.65) — the real gap between the two events.
    for i in range(10):
        t = (i + 1) / 10
        frames.append(_full_frame(_less_test_frame(0.30 + t * 0.35, 0.90, knee_offset_x=0.05 * t)))
    # Deep-flexion plateau, fully held (20 frames).
    for _ in range(20):
        frames.append(_full_frame(_less_test_frame(0.65, 0.90, knee_offset_x=0.05)))

    result = _run(frames, "side", monkeypatch)

    assert result.initial_contact_frame is not None
    # A real, non-trivial gap — not just off-by-one from smoothing.
    assert result.initial_contact_frame < result.landing_frame - 2

    # Knee flexion at initial contact should be near-straight (knee_offset_x
    # ~0 there), and displacement to max flexion should be a real, non-zero
    # bend (knee_offset_x grows to 0.05 by the deep-flexion plateau).
    assert "less_knee_flexion_ic_left" in result.less_raw
    assert "less_knee_flexion_displacement_left" in result.less_raw
    assert result.less_raw["less_knee_flexion_ic_left"] < 15.0
    assert result.less_raw["less_knee_flexion_displacement_left"] > 5.0


def test_front_view_less_raw_includes_stance_and_contact_symmetry(monkeypatch):
    standing = {
        L_SHOULDER: (0.4, 0.25, 0.0, 1.0), R_SHOULDER: (0.6, 0.25, 0.0, 1.0),
        L_HIP: (0.4, 0.50, 0.0, 1.0), R_HIP: (0.6, 0.50, 0.0, 1.0),
        L_KNEE: (0.4, 0.70, 0.0, 1.0), R_KNEE: (0.6, 0.70, 0.0, 1.0),
        L_ANKLE: (0.4, 0.90, 0.0, 1.0), R_ANKLE: (0.6, 0.90, 0.0, 1.0),
    }
    landing = {
        L_SHOULDER: (0.4, 0.25, 0.0, 1.0), R_SHOULDER: (0.6, 0.25, 0.0, 1.0),
        L_HIP: (0.4, 0.50, 0.0, 1.0), R_HIP: (0.6, 0.50, 0.0, 1.0),
        L_KNEE: (0.44, 0.70, 0.0, 1.0), R_KNEE: (0.58, 0.70, 0.0, 1.0),
        L_ANKLE: (0.4, 0.90, 0.0, 1.0), R_ANKLE: (0.6, 0.90, 0.0, 1.0),
    }
    per_frame = _build_sequence(standing, landing)

    result = _run(per_frame, "front", monkeypatch)

    # These LESS items don't depend on IC/max-flexion separation, so the
    # existing (same-frame) builder is fine for checking they're present
    # and sane.
    assert "less_stance_width_ratio_ic" in result.less_raw
    assert result.less_raw["less_stance_width_ratio_ic"] == pytest.approx(1.0, abs=0.01)
    assert "less_foot_contact_asymmetry_frames" in result.less_raw
    assert "less_trunk_lateral_ic" in result.less_raw
    assert "less_knee_valgus_ic_left" in result.less_raw
