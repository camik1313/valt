# ============================================================
# calibration.py — measures the REAL LESS box-jump protocol setup
# (Padua DA, Marshall SW, Boling MC, Thigpen CA, Garrett WE Jr, Beutler AI.
# The Landing Error Scoring System (LESS) Is a Valid and Reliable Clinical
# Assessment Tool of Jump-Landing Biomechanics: The JUMP-ACL Study. Am J
# Sports Med. 2009;37(10):1996-2002.): jump forward off a 12in/31cm box,
# land on a mark at half the athlete's height. This measures whether that
# setup was actually followed, straight from the athlete's own body in the
# video, instead of trusting a tape measure or a manually-entered box
# height.
#
# HOW: guided capture gives two known, timed windows before the jump —
# standing on the GROUND, then standing on the BOX (see capture/page.tsx's
# phase machine) — filmed by the same static camera throughout. Within
# each window we measure the athlete's ankle height in pixels; the
# difference between the two, converted to real units using the athlete's
# self-reported height as the scale reference, IS the box height. The
# ankle position during the box window (right at the edge, about to jump)
# compared to the ankle position at landing IS the landing distance.
#
# SCALE REFERENCE, DISCLOSED HONESTLY: MediaPipe has no "top of head"
# landmark, so standing height is approximated here as ankle-to-eye-level,
# not true crown-of-head height. That means the derived scale (and
# everything computed from it: box height, landing distance) runs a few
# percent HIGH relative to the athlete's true height-implied scale. This
# is stated plainly in the result note rather than corrected with an
# invented anthropometric constant nobody could verify or cite.
#
# NOT SCORED: none of this feeds LESS item points (see risk/less.py) or
# the screening risk score (risk/scoring.py) — it's protocol-fidelity
# context for how much to trust the OTHER measurements, surfaced
# separately (see ProtocolCheck in models/schemas.py).
# ============================================================

from dataclasses import dataclass

from app.cv.landing_detector import Landmarks, refine_window

LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_EYE = 2
RIGHT_EYE = 5


@dataclass
class ProtocolCheckResult:
    box_height_cm: float | None
    landing_distance_cm: float | None
    landing_distance_target_cm: float | None
    landing_distance_delta_cm: float | None
    confident: bool
    note: str


def _avg_ankle_point(
    per_frame: list[Landmarks], start: int, end: int
) -> tuple[float, float] | None:
    """Average (x, y) ankle midpoint across frames [start, end], skipping
    any frame with no pose or missing ankle landmarks."""
    xs: list[float] = []
    ys: list[float] = []
    for i in range(start, end + 1):
        lm = per_frame[i]
        if lm is None:
            continue
        xs.append((lm[LEFT_ANKLE][0] + lm[RIGHT_ANKLE][0]) / 2.0)
        ys.append((lm[LEFT_ANKLE][1] + lm[RIGHT_ANKLE][1]) / 2.0)
    if not xs:
        return None
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _avg_eye_y(per_frame: list[Landmarks], start: int, end: int) -> float | None:
    """Average eye-level y across frames [start, end] — see module
    docstring for why eye level, not top-of-head, is the reference."""
    ys: list[float] = []
    for i in range(start, end + 1):
        lm = per_frame[i]
        if lm is None:
            continue
        ys.append((lm[LEFT_EYE][1] + lm[RIGHT_EYE][1]) / 2.0)
    if not ys:
        return None
    return sum(ys) / len(ys)


def _unmeasured(target_cm: float | None, confident: bool, note: str) -> ProtocolCheckResult:
    return ProtocolCheckResult(
        box_height_cm=None,
        landing_distance_cm=None,
        landing_distance_target_cm=target_cm,
        landing_distance_delta_cm=None,
        confident=confident,
        note=note,
    )


def compute_protocol_check(
    per_frame: list[Landmarks],
    landing_frame: int,
    athlete_height_cm: float,
    fps: float,
    ground_window_seconds: tuple[float, float],
    box_window_seconds: tuple[float, float],
) -> ProtocolCheckResult:
    """
    Measure box height and landing distance from the video, using the
    athlete's self-reported height as the only real-world measurement
    anyone has to take. See the module docstring for the method and its
    disclosed scale approximation.

    Degrades gracefully (confident=False, explanatory note, no fabricated
    numbers) whenever the calibration windows can't be resolved — this is
    purely additive context and must never block the rest of the analysis.
    """
    target_cm = round(athlete_height_cm / 2.0, 1) if athlete_height_cm > 0 else None

    if athlete_height_cm <= 0:
        return _unmeasured(None, False, "No valid athlete height was provided, so calibration was skipped.")

    def to_frame(seconds: float) -> int:
        return round(seconds * fps)

    ground_window = refine_window(
        per_frame, to_frame(ground_window_seconds[0]), to_frame(ground_window_seconds[1])
    )
    box_window = refine_window(
        per_frame, to_frame(box_window_seconds[0]), to_frame(box_window_seconds[1])
    )

    if ground_window is None or box_window is None:
        return _unmeasured(
            target_cm, False,
            "Couldn't find a stable standing period in the ground and/or box "
            "calibration windows, so box height and landing distance weren't "
            "measured for this clip.",
        )

    # ---- Scale reference: ankle-to-eye span during the GROUND window ----
    ground_ankle = _avg_ankle_point(per_frame, *ground_window)
    ground_eye_y = _avg_eye_y(per_frame, *ground_window)
    if ground_ankle is None or ground_eye_y is None:
        return _unmeasured(
            target_cm, False,
            "Ankle or eye landmarks weren't visible during the ground "
            "calibration window, so scale couldn't be established.",
        )

    span_px = abs(ground_ankle[1] - ground_eye_y)
    if span_px <= 1e-6:
        return _unmeasured(
            target_cm, False,
            "Degenerate ankle-to-eye span in the ground window; couldn't "
            "establish a scale reference.",
        )
    px_per_cm = span_px / athlete_height_cm

    # ---- Box height: how much higher the ankles sit on the box ----
    box_ankle = _avg_ankle_point(per_frame, *box_window)
    if box_ankle is None:
        return _unmeasured(
            target_cm, False,
            "Ankle landmarks weren't visible during the box calibration "
            "window, so box height wasn't measured.",
        )
    box_height_px = ground_ankle[1] - box_ankle[1]  # y shrinks going up in image coords
    box_height_cm = box_height_px / px_per_cm

    # ---- Landing distance: horizontal travel from the box edge to landing ----
    landing_lm = per_frame[landing_frame] if 0 <= landing_frame < len(per_frame) else None
    landing_distance_cm: float | None = None
    if landing_lm is not None:
        landing_x = (landing_lm[LEFT_ANKLE][0] + landing_lm[RIGHT_ANKLE][0]) / 2.0
        landing_distance_cm = abs(landing_x - box_ankle[0]) / px_per_cm

    delta_cm = None if landing_distance_cm is None else round(landing_distance_cm - target_cm, 1)

    if box_height_cm <= 0:
        confident = False
        note = (
            f"Measured box height came out at {box_height_cm:.1f}cm, which isn't "
            "physically plausible (the box window wasn't clearly elevated above "
            "the ground window), so treat this measurement with caution."
        )
    else:
        confident = True
        note = (
            f"Box height measured at {box_height_cm:.1f}cm (the LESS standard is "
            "31cm/12in). Scale is estimated from ankle-to-eye-level against "
            "self-reported height, since MediaPipe has no top-of-head landmark, "
            "which runs a few percent high relative to true standing height — "
            "treat these figures as approximate, not lab-precise."
        )
        if landing_distance_cm is not None:
            note += (
                f" Landing distance measured at {landing_distance_cm:.1f}cm "
                f"(target {target_cm:.1f}cm, half of self-reported height)."
            )

    return ProtocolCheckResult(
        box_height_cm=round(box_height_cm, 1),
        landing_distance_cm=None if landing_distance_cm is None else round(landing_distance_cm, 1),
        landing_distance_target_cm=target_cm,
        landing_distance_delta_cm=delta_cm,
        confident=confident,
        note=note,
    )
