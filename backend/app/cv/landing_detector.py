# ============================================================
# landing_detector.py — finds WHEN the athlete lands.
#
# WHY THIS MATTERS: every biomechanical measurement is taken at one
# specific moment — the landing. Correct math on the wrong frame is
# still a wrong answer. This file picks that frame.
#
# THE METHOD (a documented heuristic, not a solved problem):
#   1. Build a vertical trajectory: the average hip y for each frame.
#      (Reminder: in image coords, y grows DOWNWARD. Rising = smaller y.)
#   2. Smooth it, so single-frame landmark jitter can't fake a result.
#   3. Find the airborne peak: the frame with the SMALLEST y (highest
#      point of the jump).
#   4. After that peak, find where the body stops descending — the
#      first frame where downward velocity ends (the trough). That is
#      the landing.
#
# LIMITATION (documented honestly): this infers landing from hip motion
# in 2D video. A force plate measures impact directly; we estimate it.
# Clips with double-bounces, occlusion, or heavy camera motion can fool
# it. See the Part 5 limitations writeup.
#
# TWO DIFFERENT MOMENTS, NOT ONE (added for LESS support):
# The hip-trough frame found above is the bottom of the landing squat —
# in Landing Error Scoring System (LESS) terms, that's closest to MAXIMUM
# FLEXION, not INITIAL CONTACT. Initial contact is EARLIER: the instant
# the foot first touches the ground, while the hip is still actively
# descending into the squat that follows. detect_initial_contact() below
# finds that earlier moment by applying the same trough logic to the
# ANKLES instead of the hips — the feet stop descending (touch down)
# before the hips finish flexing into the landing. See:
#   Padua DA, Marshall SW, Boling MC, Thigpen CA, Garrett WE Jr,
#   Beutler AI. The Landing Error Scoring System (LESS) Is a Valid and
#   Reliable Clinical Assessment Tool of Jump-Landing Biomechanics: The
#   JUMP-ACL Study. Am J Sports Med. 2009;37(10):1996-2002.
# ============================================================

from dataclasses import dataclass

# MediaPipe landmark indices for the hips and ankles.
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_ANKLE = 27
RIGHT_ANKLE = 28

# A frame's landmarks: list of (x, y, z, visibility) tuples, or None
# if no pose was detected in that frame.
Landmarks = list[tuple[float, float, float, float]] | None


@dataclass
class LandingResult:
    """What the detector found."""
    landing_frame: int          # index of the landing frame
    airborne_peak_frame: int    # index of the highest point of the jump
    trajectory: list[float]     # smoothed hip-y per frame (for plotting/debug)
    confident: bool             # False if the clip looked ambiguous
    note: str                   # human-readable explanation


def hip_trajectory(per_frame: list[Landmarks]) -> list[float | None]:
    """
    Build the vertical trajectory: average hip y for each frame.

    Returns None for frames where no pose was detected, so callers can
    tell "missing" apart from a real value.
    """
    traj: list[float | None] = []
    for landmarks in per_frame:
        if landmarks is None:
            traj.append(None)
            continue
        left_y = landmarks[LEFT_HIP][1]
        right_y = landmarks[RIGHT_HIP][1]
        traj.append((left_y + right_y) / 2.0)
    return traj


def _fill_gaps(traj: list[float | None]) -> list[float]:
    """
    Replace missing frames by carrying the last known value forward.
    Simple and predictable; keeps the trajectory continuous so the
    velocity calculation doesn't break on a dropped frame.
    """
    filled: list[float] = []
    last_known: float | None = None

    for value in traj:
        if value is not None:
            last_known = value
        # If the very first frames are missing, fall back to the first
        # real value we can find (or 0.5, mid-frame, if there are none).
        if last_known is None:
            first_real = next((v for v in traj if v is not None), 0.5)
            filled.append(first_real)
        else:
            filled.append(last_known)
    return filled


def smooth(values: list[float], window: int = 5) -> list[float]:
    """
    Moving-average smoothing: replace each value with the average of
    itself and its neighbours. This removes single-frame landmark
    jitter that could otherwise fake a velocity sign change.

    window should be odd (we use the frames on each side symmetrically).
    """
    if window < 2 or len(values) < window:
        return list(values)

    half = window // 2
    smoothed: list[float] = []
    for i in range(len(values)):
        # Clamp the window at the edges of the sequence.
        start = max(0, i - half)
        end = min(len(values), i + half + 1)
        chunk = values[start:end]
        smoothed.append(sum(chunk) / len(chunk))
    return smoothed


def detect_landing(per_frame: list[Landmarks], smooth_window: int = 5) -> LandingResult:
    """
    Find the landing frame from a sequence of per-frame landmarks.

    See the module docstring for the method. Returns a LandingResult
    with the chosen frame plus context for debugging.
    """
    n = len(per_frame)
    if n == 0:
        return LandingResult(0, 0, [], False, "No frames provided.")

    # 1) Trajectory, gaps filled, then smoothed.
    raw = hip_trajectory(per_frame)
    detected_count = sum(1 for v in raw if v is not None)
    filled = _fill_gaps(raw)
    traj = smooth(filled, smooth_window)

    # If we barely detected a body, don't pretend we know anything.
    if detected_count < max(5, n * 0.3):
        return LandingResult(
            landing_frame=n // 2,
            airborne_peak_frame=0,
            trajectory=traj,
            confident=False,
            note=(
                f"Pose detected in only {detected_count}/{n} frames. "
                "Landing frame is a fallback guess. Re-film with the whole "
                "body in frame and good lighting."
            ),
        )

    # 2) Airborne peak = smallest y (highest point in the image).
    peak_frame = min(range(n), key=lambda i: traj[i])

    # 3) After the peak, walk forward to find where the descent ends.
    #    Velocity = change in y between consecutive frames.
    #    Positive velocity = moving DOWN (y growing). We want the first
    #    frame after the peak where the body stops going down.
    landing_frame = None
    for i in range(peak_frame + 1, n - 1):
        velocity = traj[i + 1] - traj[i]
        if velocity <= 0:
            # Body stopped descending here -> this is the trough.
            landing_frame = i
            break

    # 4) Fallbacks: if the body never stopped descending in-frame (clip
    #    cut short), use the lowest point after the peak.
    if landing_frame is None:
        after_peak = range(peak_frame + 1, n)
        if len(list(after_peak)) == 0:
            return LandingResult(
                landing_frame=peak_frame,
                airborne_peak_frame=peak_frame,
                trajectory=traj,
                confident=False,
                note=(
                    "The highest point is the last frame, so the clip may end "
                    "before the landing. Re-film including the full landing."
                ),
            )
        landing_frame = max(after_peak, key=lambda i: traj[i])
        return LandingResult(
            landing_frame=landing_frame,
            airborne_peak_frame=peak_frame,
            trajectory=traj,
            confident=False,
            note=(
                "No clear end-of-descent found; used the lowest point after "
                "the jump instead. Check the chosen frame visually."
            ),
        )

    # A sanity check on how much the body actually moved. If the hips
    # barely changed height, this may not be a real jump at all.
    rise = traj[peak_frame]
    drop = traj[landing_frame]
    movement = abs(drop - rise)
    confident = movement > 0.02  # ~2% of frame height; deliberately lenient

    note = (
        f"Landing detected at frame {landing_frame} "
        f"(jump peak at frame {peak_frame}, vertical travel {movement:.3f} "
        f"of frame height)."
    )
    if not confident:
        note += (
            " Vertical movement was very small, so confirm this clip contains "
            "an actual jump landing."
        )

    return LandingResult(
        landing_frame=landing_frame,
        airborne_peak_frame=peak_frame,
        trajectory=traj,
        confident=confident,
        note=note,
    )


def find_standing_window(
    per_frame: list[Landmarks],
    airborne_peak_frame: int,
    min_len: int = 8,
) -> tuple[int, int] | None:
    """
    Find a STANDING window: a run of frames BEFORE the jump where the hips
    barely move vertically. That window is the athlete's own baseline —
    same body, stance, and camera setup as the landing, which is exactly
    what we need to cancel perspective and anatomy from the valgus index.

    Returns (start_frame, end_frame) inclusive, or None if no stable
    standing period exists (e.g. a jump-only clip with no lead-in).

    METHOD: look only at frames before the jump peak. Compute frame-to-frame
    vertical speed of the hips. A "standing" stretch is a maximal run of
    consecutive frames whose speed stays below a small threshold. We take
    the longest such run if it is at least `min_len` frames.
    """
    if airborne_peak_frame < min_len:
        return None  # not enough lead-in before the jump

    raw = hip_trajectory(per_frame)
    filled = _fill_gaps(raw)
    traj = smooth(filled, window=5)

    # Only consider the pre-jump portion.
    region = traj[:airborne_peak_frame]
    if len(region) < min_len:
        return None

    # Frame-to-frame vertical speed.
    speeds = [abs(region[i + 1] - region[i]) for i in range(len(region) - 1)]
    if not speeds:
        return None

    # "Barely moving" = speed below a small fraction of the total jump travel,
    # so the threshold scales with the clip rather than being a magic number.
    jump_travel = max(traj) - min(traj)
    threshold = max(0.002, jump_travel * 0.05)

    # Find the longest run of consecutive low-speed frames.
    best_start = best_end = None
    best_len = 0
    run_start = 0
    for i in range(len(speeds) + 1):
        moving = i == len(speeds) or speeds[i] > threshold
        if moving:
            run_len = i - run_start
            if run_len > best_len:
                best_len = run_len
                best_start, best_end = run_start, i  # frames [run_start, i]
            run_start = i + 1

    if best_len >= min_len and best_start is not None:
        # end index in speeds maps to frame best_end (inclusive of that frame).
        return (best_start, min(best_end, airborne_peak_frame - 1))
    return None


# ============================================================
# INITIAL CONTACT (for LESS) — a second, earlier landmark event than the
# max-flexion frame found above. See the module docstring.
# ============================================================

@dataclass
class InitialContactResult:
    """What detect_initial_contact found."""
    frame: int             # index of the initial-contact frame
    confident: bool        # False if the two moments couldn't be separated
    note: str


def ankle_trajectory(per_frame: list[Landmarks]) -> list[float | None]:
    """
    Average ankle y per frame. The ankles stop descending (touch down)
    BEFORE the hips finish descending into the landing squat, so this
    trajectory's trough comes earlier than the hip trajectory's — that
    gap is exactly the difference between "initial contact" and "maximum
    flexion" in LESS terms.
    """
    traj: list[float | None] = []
    for landmarks in per_frame:
        if landmarks is None:
            traj.append(None)
            continue
        left_y = landmarks[LEFT_ANKLE][1]
        right_y = landmarks[RIGHT_ANKLE][1]
        traj.append((left_y + right_y) / 2.0)
    return traj


def _first_trough_frame(traj: list[float], start: int, end: int) -> int | None:
    """
    Walk forward from `start`, return the first index i (start <= i < end)
    where the trajectory stops increasing (velocity traj[i+1]-traj[i] <= 0).
    Shared logic behind both detect_landing's hip trough and the ankle-
    based initial-contact search below.
    """
    for i in range(start, end):
        if traj[i + 1] - traj[i] <= 0:
            return i
    return None


def detect_initial_contact(
    per_frame: list[Landmarks],
    airborne_peak_frame: int,
    max_flexion_frame: int,
    smooth_window: int = 3,
) -> InitialContactResult:
    """
    Find INITIAL CONTACT: the first moment the feet touch the ground after
    the airborne phase. Searched only between the jump peak and the
    already-detected max-flexion frame, so initial contact can never land
    after max flexion — it's always at or before it, matching real landing
    mechanics (the foot plants, THEN the knee/hip/trunk keep flexing to
    absorb the impact).
    """
    if max_flexion_frame <= airborne_peak_frame + 1:
        return InitialContactResult(
            frame=max_flexion_frame,
            confident=False,
            note=(
                "No room between the jump peak and the max-flexion frame to "
                "separately locate initial contact; using the same frame for both."
            ),
        )

    raw = ankle_trajectory(per_frame)
    filled = _fill_gaps(raw)
    traj = smooth(filled, smooth_window)

    search_end = min(max_flexion_frame, len(traj) - 1)
    contact = _first_trough_frame(traj, airborne_peak_frame + 1, search_end)

    if contact is not None:
        return InitialContactResult(
            frame=contact,
            confident=True,
            note=(
                f"Initial contact detected at frame {contact} (ankles stop "
                f"descending here); maximum flexion follows at frame "
                f"{max_flexion_frame}."
            ),
        )

    return InitialContactResult(
        frame=max_flexion_frame,
        confident=False,
        note=(
            "Could not separate initial contact from maximum flexion in "
            "this clip (the ankles never stopped descending before the "
            "hip trough); using the same frame for both."
        ),
    )


def detect_per_leg_contact(
    per_frame: list[Landmarks],
    airborne_peak_frame: int,
    max_flexion_frame: int,
    smooth_window: int = 3,
) -> dict[str, int | None]:
    """
    Find EACH leg's own initial-contact frame independently (left ankle
    vs right ankle), for LESS item 8 ("initial foot contact: symmetrical").
    Returns {"left": frame|None, "right": frame|None} — None if that
    ankle's trajectory never resolves to a clear touchdown in the search
    window.
    """
    if max_flexion_frame <= airborne_peak_frame + 1:
        return {"left": None, "right": None}

    search_end = min(max_flexion_frame, len(per_frame) - 1)
    result: dict[str, int | None] = {}

    for side, index in (("left", LEFT_ANKLE), ("right", RIGHT_ANKLE)):
        raw: list[float | None] = [
            (lm[index][1] if lm is not None else None) for lm in per_frame
        ]
        filled = _fill_gaps(raw)
        traj = smooth(filled, smooth_window)
        result[side] = _first_trough_frame(traj, airborne_peak_frame + 1, search_end)

    return result
