# ============================================================
# test_calibration.py — proves compute_protocol_check() correctly derives
# real-world box height and landing distance from synthetic pose data with
# hand-computed expected values, and degrades gracefully (confident=False,
# no exception) when a calibration window can't be resolved.
#
# STRATEGY: same synthetic-landmark-sequence technique as test_pipeline.py
# — build frames with known landmark positions rather than a real video or
# MediaPipe, and hand-verify the math independently of the implementation.
# ============================================================

from app.cv import calibration

L_ANKLE, R_ANKLE = 27, 28
L_EYE, R_EYE = 2, 5

FPS = 10.0
GROUND_WINDOW_SECONDS = (0.0, 3.0)   # -> frames [0, 30)
BOX_WINDOW_SECONDS = (3.0, 6.0)      # -> frames [30, 60)
LANDING_FRAME = 70

GROUND_ANKLE_Y = 0.90
GROUND_EYE_Y = 0.30      # ankle-to-eye span = 0.60
BOX_ANKLE_Y = 0.75       # 0.15 higher (smaller y) than ground -> the box
BOX_ANKLE_X = 0.50       # where their feet were, at the box edge
LANDING_ANKLE_X = 0.60   # 0.10 horizontal travel from the box edge
LANDING_ANKLE_Y = 0.95

ATHLETE_HEIGHT_CM = 170.0
# px_per_cm = span_px / height_cm = 0.60 / 170
PX_PER_CM = 0.60 / ATHLETE_HEIGHT_CM
EXPECTED_BOX_HEIGHT_CM = round((GROUND_ANKLE_Y - BOX_ANKLE_Y) / PX_PER_CM, 1)  # 42.5
EXPECTED_LANDING_DISTANCE_CM = round(abs(LANDING_ANKLE_X - BOX_ANKLE_X) / PX_PER_CM, 1)  # 28.3
EXPECTED_TARGET_CM = round(ATHLETE_HEIGHT_CM / 2.0, 1)  # 85.0


def _frame(ankle_xy: tuple[float, float], eye_y: float = 0.5):
    """33 MediaPipe landmarks; only ankles/eyes are populated meaningfully."""
    frame = [(0.5, 0.5, 0.0, 1.0)] * 33
    frame[L_ANKLE] = (ankle_xy[0], ankle_xy[1], 0.0, 1.0)
    frame[R_ANKLE] = (ankle_xy[0], ankle_xy[1], 0.0, 1.0)
    frame[L_EYE] = (0.5, eye_y, 0.0, 1.0)
    frame[R_EYE] = (0.5, eye_y, 0.0, 1.0)
    return frame


def _build_clean_sequence() -> list:
    frames = []
    for _ in range(30):  # ground window: frames 0-29
        frames.append(_frame((0.5, GROUND_ANKLE_Y), eye_y=GROUND_EYE_Y))
    for _ in range(30):  # box window: frames 30-59
        frames.append(_frame((BOX_ANKLE_X, BOX_ANKLE_Y)))
    for _ in range(10):  # filler: frames 60-69 (airborne, not used by calibration)
        frames.append(_frame((BOX_ANKLE_X, 0.4)))
    frames.append(_frame((LANDING_ANKLE_X, LANDING_ANKLE_Y)))  # frame 70: landing
    return frames


def test_clean_sequence_measures_box_height_and_landing_distance():
    per_frame = _build_clean_sequence()

    result = calibration.compute_protocol_check(
        per_frame,
        landing_frame=LANDING_FRAME,
        athlete_height_cm=ATHLETE_HEIGHT_CM,
        fps=FPS,
        ground_window_seconds=GROUND_WINDOW_SECONDS,
        box_window_seconds=BOX_WINDOW_SECONDS,
    )

    assert result.confident is True
    assert result.box_height_cm == EXPECTED_BOX_HEIGHT_CM
    assert result.landing_distance_cm == EXPECTED_LANDING_DISTANCE_CM
    assert result.landing_distance_target_cm == EXPECTED_TARGET_CM
    assert result.landing_distance_delta_cm == round(
        EXPECTED_LANDING_DISTANCE_CM - EXPECTED_TARGET_CM, 1
    )
    assert "42.5" in result.note


def test_no_stable_box_window_degrades_without_raising():
    # Ground window is stable, but the "box" window jitters wildly (e.g. the
    # athlete never actually settled on the box) -> refine_window should
    # find no qualifying run, and compute_protocol_check should degrade to
    # confident=False with an explanatory note, not raise or fabricate.
    frames = []
    for _ in range(30):  # stable ground window
        frames.append(_frame((0.5, GROUND_ANKLE_Y), eye_y=GROUND_EYE_Y))
    for i in range(30):  # jittery "box" window: alternates wildly, never settles
        y = BOX_ANKLE_Y + (0.3 if i % 2 == 0 else -0.3)
        frames.append(_frame((BOX_ANKLE_X, y)))
    frames.append(_frame((LANDING_ANKLE_X, LANDING_ANKLE_Y)))

    result = calibration.compute_protocol_check(
        frames,
        landing_frame=len(frames) - 1,
        athlete_height_cm=ATHLETE_HEIGHT_CM,
        fps=FPS,
        ground_window_seconds=GROUND_WINDOW_SECONDS,
        box_window_seconds=BOX_WINDOW_SECONDS,
    )

    assert result.confident is False
    assert result.box_height_cm is None
    assert result.landing_distance_cm is None
    # Target is still reported (pure arithmetic on self-reported height,
    # doesn't depend on the video at all).
    assert result.landing_distance_target_cm == EXPECTED_TARGET_CM


def test_missing_height_skips_calibration_without_raising():
    per_frame = _build_clean_sequence()

    result = calibration.compute_protocol_check(
        per_frame,
        landing_frame=LANDING_FRAME,
        athlete_height_cm=0.0,
        fps=FPS,
        ground_window_seconds=GROUND_WINDOW_SECONDS,
        box_window_seconds=BOX_WINDOW_SECONDS,
    )

    assert result.confident is False
    assert result.box_height_cm is None
    assert result.landing_distance_target_cm is None
