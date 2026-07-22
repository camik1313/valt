# ============================================================
# pipeline.py — THE REAL PIPELINE (view-aware).
#
#     video + view → pose_estimator → landing_detector → metrics
#
# THE CENTRAL SCIENTIFIC POINT:
# Human motion happens in anatomical PLANES, and a 2D camera can only
# see the plane it faces:
#
#   FRONT view  → FRONTAL plane  → knee valgus, lateral trunk lean
#   SIDE view   → SAGITTAL plane → knee flexion, hip flexion, forward lean
#
# A knee bending forward is nearly INVISIBLE to a front-on camera (hip,
# knee and ankle project onto a near-vertical line). So "knee flexion"
# measured from the front is projection noise, not biomechanics. This
# pipeline therefore reports ONLY the measurements that are valid for
# the camera view it was given, rather than inventing the rest.
#
# Note the elegant consequence: `180 - (hip-knee-ankle angle)` is the
# SAME arithmetic for both. From the front it means valgus; from the
# side it means flexion. The math doesn't change — the meaning does.
#
# LANDMARK INDICES: 11/12 shoulders, 23/24 hips, 25/26 knees, 27/28 ankles.
# "Left"/"right" are the SUBJECT'S anatomical sides.
# ============================================================

from dataclasses import dataclass, field

from app.cv import metrics, pose_estimator
from app.cv.landing_detector import detect_landing, find_standing_window

L_SHOULDER, R_SHOULDER = 11, 12
L_HIP, R_HIP = 23, 24
L_KNEE, R_KNEE = 25, 26
L_ANKLE, R_ANKLE = 27, 28

# MediaPipe reports 0..1 confidence that a joint is really visible.
# Below this we don't trust it (occluded, out of frame, motion blur).
MIN_VISIBILITY = 0.5

# The two camera views we support.
VIEW_FRONT = "front"
VIEW_SIDE = "side"

# Which measurements are VALID for each view. This mapping is the
# scientific contract of the whole file.
VALID_MEASUREMENTS = {
    VIEW_FRONT: [
        "knee_valgus_left",     # horizontal index, hip-widths (+ = medial/valgus)
        "knee_valgus_right",
        "valgus_asymmetry",     # difference between legs (perspective-robust)
        "kasr",                 # knee/ankle separation ratio
        "trunk_lean_lateral",
    ],
    VIEW_SIDE: [
        "knee_flexion_left",
        "knee_flexion_right",
        "hip_flexion_left",
        "hip_flexion_right",
        "flexion_asymmetry",
        "trunk_lean_forward",
    ],
}


@dataclass
class PipelineResult:
    """Output shape shared with mock_pipeline so the two are swappable."""
    landing_frame: int
    measurements: dict[str, float]
    view: str = VIEW_FRONT
    landmark_count: int = 33
    notes: list[str] = field(default_factory=list)
    confident: bool = True


def _point(landmarks, index: int) -> tuple[float, float]:
    """The (x, y) of one landmark. We ignore z — this is 2D analysis."""
    x, y, _z, _vis = landmarks[index]
    return (x, y)


def _visible(landmarks, *indices: int) -> bool:
    """True only if every listed landmark clears the visibility bar."""
    return all(landmarks[i][3] >= MIN_VISIBILITY for i in indices)


def _midpoint(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _nearest_valid_frame(per_frame, target: int) -> int | None:
    """Search outward from `target` for the closest frame that has landmarks."""
    n = len(per_frame)
    for offset in range(n):
        for idx in (target - offset, target + offset):
            if 0 <= idx < n and per_frame[idx] is not None:
                return idx
    return None


def run_pipeline(seed: str, video_path: str, view: str = VIEW_FRONT) -> PipelineResult:
    """
    Analyze a jump-landing video from a known camera view.

    Args:
        seed: unused (kept so the signature matches mock_pipeline).
        video_path: the video file on disk.
        view: "front" or "side". Determines which measurements are valid
            and therefore which ones we compute at all.

    Raises:
        ValueError: unreadable video, no pose found, or an unknown view.
    """
    view = view.lower()
    if view not in (VIEW_FRONT, VIEW_SIDE):
        raise ValueError(f"view must be '{VIEW_FRONT}' or '{VIEW_SIDE}', got '{view}'")

    notes: list[str] = []

    # ---- 1) Landmarks for every frame ----
    extraction = pose_estimator.extract_landmarks(video_path)
    if extraction.frames_with_pose == 0:
        raise ValueError(
            "No body was detected in this video. Make sure the whole body is "
            "in frame with good lighting, then try again."
        )

    notes.append(
        f"Pose detected in {extraction.frames_with_pose}/{extraction.frames_read} "
        f"frames ({extraction.detection_rate:.0%})."
    )
    if extraction.detection_rate < 0.7:
        notes.append(
            "Detection rate was low, so these measurements are less reliable. "
            "Re-filming with the full body in frame and fitted clothing helps."
        )

    # ---- 2) The landing frame ----
    landing = detect_landing(extraction.per_frame)
    notes.append(landing.note)

    landmarks = extraction.per_frame[landing.landing_frame]
    if landmarks is None:
        nearest = _nearest_valid_frame(extraction.per_frame, landing.landing_frame)
        if nearest is None:
            raise ValueError("No usable pose data near the detected landing frame.")
        landmarks = extraction.per_frame[nearest]
        notes.append(f"No pose on the landing frame; used nearest valid frame {nearest}.")

    # ---- 3) Measure — ONLY what this view can actually see ----
    measurements: dict[str, float] = {}
    left_leg_ok = _visible(landmarks, L_HIP, L_KNEE, L_ANKLE)
    right_leg_ok = _visible(landmarks, R_HIP, R_KNEE, R_ANKLE)

    if not left_leg_ok and not right_leg_ok:
        raise ValueError(
            "Neither leg was clearly visible at the landing frame. Re-film with "
            "the full body in view."
        )

    shoulders_ok = _visible(landmarks, L_SHOULDER, R_SHOULDER, L_HIP, R_HIP)
    shoulder_mid = _midpoint(_point(landmarks, L_SHOULDER), _point(landmarks, R_SHOULDER))
    hip_mid = _midpoint(_point(landmarks, L_HIP), _point(landmarks, R_HIP))

    if view == VIEW_FRONT:
        # --- FRONTAL PLANE: valgus (horizontal index) + lateral lean ---
        # Helper: compute per-leg valgus index at a given frame's landmarks.
        def valgus_at(fr_landmarks):
            lh, rh = _point(fr_landmarks, L_HIP), _point(fr_landmarks, R_HIP)
            hw = metrics.hip_width(lh, rh)
            out = {}
            if _visible(fr_landmarks, L_HIP, L_KNEE, L_ANKLE):
                out["left"] = metrics.knee_valgus_index(
                    lh, _point(fr_landmarks, L_KNEE), _point(fr_landmarks, L_ANKLE), hw, "left"
                )
            if _visible(fr_landmarks, R_HIP, R_KNEE, R_ANKLE):
                out["right"] = metrics.knee_valgus_index(
                    rh, _point(fr_landmarks, R_KNEE), _point(fr_landmarks, R_ANKLE), hw, "right"
                )
            return out

        def kasr_at(fr_landmarks):
            if not _visible(fr_landmarks, L_KNEE, R_KNEE, L_ANKLE, R_ANKLE):
                return None
            return metrics.knee_ankle_separation_ratio(
                _point(fr_landmarks, L_KNEE), _point(fr_landmarks, R_KNEE),
                _point(fr_landmarks, L_ANKLE), _point(fr_landmarks, R_ANKLE),
            )

        landing_valgus = valgus_at(landmarks)
        landing_kasr = kasr_at(landmarks)

        # --- Try to find a standing baseline in the same clip ---
        window = find_standing_window(extraction.per_frame, landing.airborne_peak_frame)
        baseline_applied = False
        base_valgus = {"left": 0.0, "right": 0.0}
        base_kasr = None

        if window is not None:
            start, end = window
            # Average the index across the standing frames (kills jitter).
            l_vals, r_vals, kasr_vals = [], [], []
            for i in range(start, end + 1):
                fr = extraction.per_frame[i]
                if fr is None:
                    continue
                v = valgus_at(fr)
                if "left" in v:
                    l_vals.append(v["left"])
                if "right" in v:
                    r_vals.append(v["right"])
                k = kasr_at(fr)
                if k is not None:
                    kasr_vals.append(k)
            if l_vals:
                base_valgus["left"] = sum(l_vals) / len(l_vals)
            if r_vals:
                base_valgus["right"] = sum(r_vals) / len(r_vals)
            if kasr_vals:
                base_kasr = sum(kasr_vals) / len(kasr_vals)
            baseline_applied = True
            notes.append(
                f"Standing baseline found (frames {start}-{end}); valgus reported "
                f"as CHANGE from standing to landing (cancels stance and camera "
                f"perspective)."
            )
        else:
            notes.append(
                "No standing baseline in this clip, so valgus is UNCORRECTED — "
                "camera perspective may inflate it. Film a few seconds of standing "
                "before the jump (the guided capture does this automatically). "
                "Left/right asymmetry is still reliable without a baseline."
            )

        # Report the baseline-corrected value where possible.
        if "left" in landing_valgus:
            measurements["knee_valgus_left"] = round(
                landing_valgus["left"] - base_valgus["left"], 3
            )
        if "right" in landing_valgus:
            measurements["knee_valgus_right"] = round(
                landing_valgus["right"] - base_valgus["right"], 3
            )
        if "knee_valgus_left" in measurements and "knee_valgus_right" in measurements:
            measurements["valgus_asymmetry"] = round(
                metrics.asymmetry_percent(
                    landing_valgus["left"], landing_valgus["right"]
                ), 1,
            )
        else:
            notes.append("Only one leg was visible; asymmetry could not be measured.")

        if landing_kasr is not None:
            kasr_value = landing_kasr - (base_kasr if base_kasr is not None else 0.0) + (
                1.0 if base_kasr is not None else 0.0
            )
            # If baseline exists, express KASR relative to standing (standing = 1.0).
            measurements["kasr"] = round(kasr_value, 3)

        if shoulders_ok:
            measurements["trunk_lean_lateral"] = round(
                metrics.lateral_trunk_lean(shoulder_mid, hip_mid), 1
            )

        notes.append(
            "Front view: measuring the FRONTAL plane (knee valgus, lateral lean). "
            "Knee/hip flexion are sagittal-plane motions and cannot be measured "
            "from this angle — film from the side for those."
        )

    else:  # VIEW_SIDE
        # --- SAGITTAL PLANE: flexion and forward lean ---
        if left_leg_ok:
            measurements["knee_flexion_left"] = round(
                metrics.knee_flexion(
                    _point(landmarks, L_HIP), _point(landmarks, L_KNEE), _point(landmarks, L_ANKLE)
                ), 1,
            )
        if right_leg_ok:
            measurements["knee_flexion_right"] = round(
                metrics.knee_flexion(
                    _point(landmarks, R_HIP), _point(landmarks, R_KNEE), _point(landmarks, R_ANKLE)
                ), 1,
            )

        if "knee_flexion_left" in measurements and "knee_flexion_right" in measurements:
            measurements["flexion_asymmetry"] = round(
                metrics.asymmetry_percent(
                    measurements["knee_flexion_left"], measurements["knee_flexion_right"]
                ), 1,
            )

        if _visible(landmarks, L_SHOULDER, L_HIP, L_KNEE):
            measurements["hip_flexion_left"] = round(
                metrics.hip_flexion(
                    _point(landmarks, L_SHOULDER), _point(landmarks, L_HIP), _point(landmarks, L_KNEE)
                ), 1,
            )
        if _visible(landmarks, R_SHOULDER, R_HIP, R_KNEE):
            measurements["hip_flexion_right"] = round(
                metrics.hip_flexion(
                    _point(landmarks, R_SHOULDER), _point(landmarks, R_HIP), _point(landmarks, R_KNEE)
                ), 1,
            )

        if shoulders_ok:
            measurements["trunk_lean_forward"] = round(
                metrics.trunk_lean(shoulder_mid, hip_mid), 1
            )

        notes.append(
            "Side view: measuring the SAGITTAL plane (knee/hip flexion, forward lean). "
            "Knee valgus is a frontal-plane motion and cannot be measured from this "
            "angle — film from the front for that."
        )
        notes.append(
            "From the side, the near leg blocks the far leg, so the far leg's values "
            "are less reliable. Treat the near-side leg as the measured one."
        )

    return PipelineResult(
        landing_frame=landing.landing_frame,
        measurements=measurements,
        view=view,
        landmark_count=33,
        notes=notes,
        confident=landing.confident and extraction.detection_rate >= 0.7,
    )
