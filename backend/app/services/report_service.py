# ============================================================
# report_service.py — turns a video into a finished Analysis.
#
# Division of labor (unchanged):
#   cv/pipeline    -> RAW measurements (the science)
#   report_service -> INTERPRETATION (banding, summary, assembling schema)
#
# VIEW-AWARE: the pipeline only returns measurements valid for the camera
# angle, so this file just labels and bands whatever it gets back. No
# averaging across legs — asymmetry is the point, and averaging hides it.
# ============================================================

from app.models.schemas import Analysis, Metric
from app.services import storage
from app.cv import pipeline, mock_pipeline

# Set False to force the mock pipeline (instant, fake numbers).
USE_REAL_PIPELINE = True

# Human-friendly labels + units, keyed by measurement name.
LABELS = {
    # Frontal plane (front view)
    "knee_valgus_left": ("Knee valgus — left", "deg"),
    "knee_valgus_right": ("Knee valgus — right", "deg"),
    "valgus_asymmetry": ("Valgus asymmetry", "%"),
    "trunk_lean_lateral": ("Trunk lean (lateral)", "deg"),
    # Sagittal plane (side view)
    "knee_flexion_left": ("Knee flexion — left", "deg"),
    "knee_flexion_right": ("Knee flexion — right", "deg"),
    "hip_flexion_left": ("Hip flexion — left", "deg"),
    "hip_flexion_right": ("Hip flexion — right", "deg"),
    "flexion_asymmetry": ("Flexion asymmetry", "%"),
    "trunk_lean_forward": ("Trunk lean (forward)", "deg"),
    # Mock-only keys (fallback path)
    "knee_flexion": ("Knee flexion", "deg"),
    "knee_valgus": ("Dynamic knee valgus", "deg"),
    "trunk_lean": ("Trunk lean", "deg"),
    "asymmetry": ("Left / right asymmetry", "%"),
    "hip_flexion": ("Hip flexion", "deg"),
}

# Display order. We show whatever exists, in this order.
DISPLAY_ORDER = [
    "knee_valgus_left", "knee_valgus_right", "valgus_asymmetry", "trunk_lean_lateral",
    "knee_flexion_left", "knee_flexion_right", "flexion_asymmetry",
    "hip_flexion_left", "hip_flexion_right", "trunk_lean_forward",
    "knee_flexion", "knee_valgus", "trunk_lean", "asymmetry", "hip_flexion",
]

# ILLUSTRATIVE banding thresholds (watch_at, flag_at) applied to the
# ABSOLUTE value. PLACEHOLDERS — Part 5 replaces these with values cited
# from ACL injury-prevention literature.
THRESHOLDS = {
    "knee_valgus_left": (10, 15),
    "knee_valgus_right": (10, 15),
    "knee_valgus": (10, 15),
    "trunk_lean_lateral": (10, 15),
    "trunk_lean_forward": (30, 45),
    "trunk_lean": (10, 15),
    "valgus_asymmetry": (25, 50),
    "flexion_asymmetry": (10, 15),
    "asymmetry": (10, 15),
}


def _band(key: str, value: float) -> str:
    """Convert a raw measurement into ok / watch / flag."""
    # Flexion is inverted: LOW flexion (a stiff landing) is the concern.
    if key.startswith("knee_flexion") or key.startswith("hip_flexion"):
        deficit = 70 - value  # degrees under a ~70 deg soft landing
        if deficit >= 15:
            return "flag"
        if deficit >= 8:
            return "watch"
        return "ok"

    if key in THRESHOLDS:
        watch_at, flag_at = THRESHOLDS[key]
        # Valgus is signed: negative = varus. We band on MAGNITUDE, since
        # deviation in either direction is worth noticing.
        v = abs(value)
        if v >= flag_at:
            return "flag"
        if v >= watch_at:
            return "watch"
        return "ok"

    return "ok"


def build_analysis(
    upload_id: str,
    athlete_name: str,
    video_filename: str,
    video_path: str | None = None,
    view: str = "front",
) -> Analysis:
    """
    Run the pipeline on a video and assemble a full Analysis.

    Falls back to the mock if the real pipeline fails, clearly labeled so
    simulated numbers can never be mistaken for measurements.
    """
    used_mock = False
    fallback_reason = ""

    # ---- 1) Raw measurements ----
    if USE_REAL_PIPELINE and video_path:
        try:
            result = pipeline.run_pipeline(seed=upload_id, video_path=video_path, view=view)
        except Exception as exc:
            result = mock_pipeline.run_pipeline(seed=upload_id)
            used_mock = True
            fallback_reason = str(exc)
    else:
        result = mock_pipeline.run_pipeline(seed=upload_id)
        used_mock = True
        fallback_reason = "Real pipeline disabled."

    # ---- 2) Label and band ----
    metrics_list: list[Metric] = []
    for key in DISPLAY_ORDER:
        if key not in result.measurements:
            continue
        value = result.measurements[key]
        label, unit = LABELS.get(key, (key, ""))
        metrics_list.append(
            Metric(key=key, label=label, value=value, unit=unit, status=_band(key, value))
        )

    # ---- 3) Summary ----
    flags = [m.label for m in metrics_list if m.status == "flag"]
    watches = [m.label for m in metrics_list if m.status == "watch"]
    plane = "frontal plane" if view == "front" else "sagittal plane"

    if used_mock:
        summary = (
            f"⚠️ SIMULATED RESULT for {athlete_name}. The video could not be "
            f"analyzed ({fallback_reason}), so these numbers are placeholders, "
            f"not measurements. Re-film with the whole body in frame."
        )
    elif flags:
        summary = (
            f"Analysis complete for {athlete_name} ({view} view, {plane}). "
            f"Measured at the landing frame. The following stood out and may be "
            f"worth a closer look: {', '.join(flags)}. These are movement "
            f"observations from an automated tool, not a diagnosis."
        )
    elif watches:
        summary = (
            f"Analysis complete for {athlete_name} ({view} view, {plane}). "
            f"Most patterns look typical; {', '.join(watches)} sat near the "
            f"borderline. These are movement observations, not a diagnosis."
        )
    else:
        summary = (
            f"Analysis complete for {athlete_name} ({view} view, {plane}). "
            f"All measured patterns fell within typical ranges for this landing. "
            f"These are movement observations, not a diagnosis."
        )

    if not used_mock and result.notes:
        summary += " " + " ".join(result.notes)

    # ---- 4) Assemble ----
    return Analysis(
        id=storage.new_analysis_id(),
        athlete_name=athlete_name,
        created_at=storage.now_iso(),
        video_filename=video_filename,
        view=view,
        metrics=metrics_list,
        summary=summary,
    )
