# ============================================================
# report_service.py — turns an uploaded video into an Analysis.
#
# For now it produces MOCK metrics with plausible values. This is
# the seam where the real science plugs in later: in Stage 6/7 the
# body of build_analysis() will call the CV pipeline (cv/) to get
# REAL measurements. The function's inputs and outputs won't change,
# so the routes and the frontend never need to be touched.
#
# The status banding thresholds below are ILLUSTRATIVE placeholders,
# not clinical cutoffs. Real, cited thresholds come with Stage 7.
# ============================================================

import random

from app.models.schemas import Analysis, Metric
from app.services import storage


def _band(value: float, watch_at: float, flag_at: float) -> str:
    """
    Convert a number into a status band.
    Higher value = more concern, for these illustrative metrics.
    """
    if value >= flag_at:
        return "flag"
    if value >= watch_at:
        return "watch"
    return "ok"


def build_analysis(upload_id: str, filename: str, athlete_name: str) -> Analysis:
    """
    Create a full Analysis for an uploaded video.

    MOCK for now: we seed the random generator with the upload_id so
    the same upload always yields the same numbers (stable for demos),
    while different uploads look different.
    """
    rng = random.Random(upload_id)  # deterministic per upload

    # --- Generate plausible mock measurements ---
    knee_flexion = round(rng.uniform(55, 95), 1)     # degrees
    knee_valgus = round(rng.uniform(3, 20), 1)       # degrees (higher = more inward)
    trunk_lean = round(rng.uniform(2, 18), 1)        # degrees
    asymmetry = round(rng.uniform(2, 22), 1)         # percent difference L/R
    hip_flexion = round(rng.uniform(40, 90), 1)      # degrees

    metrics = [
        Metric(key="knee_flexion", label="Knee flexion", value=knee_flexion,
               unit="deg", status=_band(65 - knee_flexion + 15, 8, 16)),
        Metric(key="knee_valgus", label="Dynamic knee valgus", value=knee_valgus,
               unit="deg", status=_band(knee_valgus, 10, 15)),
        Metric(key="trunk_lean", label="Trunk lean", value=trunk_lean,
               unit="deg", status=_band(trunk_lean, 10, 15)),
        Metric(key="asymmetry", label="Left / right asymmetry", value=asymmetry,
               unit="%", status=_band(asymmetry, 10, 15)),
        Metric(key="hip_flexion", label="Hip flexion", value=hip_flexion,
               unit="deg", status="ok"),
    ]

    # --- Write a short plain-language summary ---
    flags = [m.label for m in metrics if m.status == "flag"]
    if flags:
        summary = (
            f"Analysis complete for {athlete_name}. Most measurements fall within "
            f"typical ranges, but the following stood out and may be worth a closer "
            f"look: {', '.join(flags)}. These are movement observations, not a diagnosis."
        )
    else:
        summary = (
            f"Analysis complete for {athlete_name}. All measured patterns fell within "
            f"typical ranges for this landing. These are movement observations, "
            f"not a diagnosis."
        )

    # --- Assemble and return the Analysis object ---
    return Analysis(
        id=storage.new_analysis_id(),
        athlete_name=athlete_name,
        created_at=storage.now_iso(),
        video_filename=filename,
        metrics=metrics,
        summary=summary,
    )
