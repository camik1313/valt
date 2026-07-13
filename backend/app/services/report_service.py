# ============================================================
# report_service.py — turns a video into a finished Analysis.
#
# CHANGED IN STAGE 6: this no longer generates numbers itself. It now
# CALLS THE CV PIPELINE (cv/mock_pipeline) to get raw measurements, then
# does the "meaning" work on top: banding each measurement into ok/watch/
# flag and writing the plain-language summary.
#
# Division of labor:
#   cv/ pipeline  -> RAW measurements (the science)
#   report_service -> INTERPRETATION (banding + summary + assembling schema)
#
# When the real pipeline lands in Stage 7, only the import below changes
# (mock_pipeline -> real pipeline). Everything in this file stays the same.
# ============================================================

from app.models.schemas import Analysis, Metric
from app.services import storage
from app.cv import mock_pipeline

# Human-friendly labels + units for each measurement key.
LABELS = {
    "knee_flexion": ("Knee flexion", "deg"),
    "knee_valgus": ("Dynamic knee valgus", "deg"),
    "trunk_lean": ("Trunk lean", "deg"),
    "asymmetry": ("Left / right asymmetry", "%"),
    "hip_flexion": ("Hip flexion", "deg"),
}

# ILLUSTRATIVE banding thresholds (watch_at, flag_at). Higher = more concern.
# NOTE: these are placeholders, NOT clinical cutoffs. Cited, evidence-based
# thresholds arrive with the real pipeline in Stage 7.
THRESHOLDS = {
    "knee_valgus": (10, 15),
    "trunk_lean": (10, 15),
    "asymmetry": (10, 15),
}


def _band(key: str, value: float) -> str:
    """Convert a raw measurement into ok / watch / flag."""
    # knee_flexion is the opposite direction: LOW flexion (stiff landing)
    # is the concern, so we band on how far below a soft-landing target it is.
    if key == "knee_flexion":
        deficit = 70 - value  # how many degrees under a ~70° soft landing
        if deficit >= 15:
            return "flag"
        if deficit >= 8:
            return "watch"
        return "ok"

    if key in THRESHOLDS:
        watch_at, flag_at = THRESHOLDS[key]
        if value >= flag_at:
            return "flag"
        if value >= watch_at:
            return "watch"
        return "ok"

    return "ok"  # hip_flexion and anything else: neutral for now


def build_analysis(upload_id: str, athlete_name: str, video_filename: str) -> Analysis:
    """
    Run the pipeline and assemble a full Analysis object.
    """
    # 1) Get raw measurements from the CV pipeline (mock for now).
    result = mock_pipeline.run_pipeline(seed=upload_id)

    # 2) Turn each raw number into a labeled, banded Metric.
    metrics: list[Metric] = []
    for key in mock_pipeline.MEASUREMENT_KEYS:
        value = result.measurements[key]
        label, unit = LABELS[key]
        metrics.append(
            Metric(key=key, label=label, value=value, unit=unit, status=_band(key, value))
        )

    # 3) Write a plain-language summary based on what got flagged.
    flags = [m.label for m in metrics if m.status == "flag"]
    watches = [m.label for m in metrics if m.status == "watch"]

    if flags:
        summary = (
            f"Analysis complete for {athlete_name}. The following measurements stood "
            f"out and may be worth a closer look: {', '.join(flags)}. "
            f"These are movement observations from an automated tool, not a diagnosis."
        )
    elif watches:
        summary = (
            f"Analysis complete for {athlete_name}. Most patterns look typical; "
            f"{', '.join(watches)} sat near the borderline and could be worth monitoring. "
            f"These are movement observations, not a diagnosis."
        )
    else:
        summary = (
            f"Analysis complete for {athlete_name}. All measured patterns fell within "
            f"typical ranges for this landing. These are movement observations, not a diagnosis."
        )

    # 4) Assemble and return the Analysis.
    return Analysis(
        id=storage.new_analysis_id(),
        athlete_name=athlete_name,
        created_at=storage.now_iso(),
        video_filename=video_filename,
        metrics=metrics,
        summary=summary,
    )
