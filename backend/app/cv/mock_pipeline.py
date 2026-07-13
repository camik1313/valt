# ============================================================
# mock_pipeline.py — a STAND-IN for the real computer-vision pipeline.
#
# WHY THIS FILE MATTERS:
# The real pipeline (Stage 7) will do:
#     video → pose estimation (MediaPipe) → find landing frame →
#     compute joint angles → return measurements
#
# This mock returns the SAME SHAPE of result (a PipelineResult with a
# landing frame and a dict of measurements) but with fake numbers. Because
# the shape matches, Stage 7 swaps the internals of run_pipeline() without
# changing report_service.py, the routes, or the frontend. That is the
# entire point of putting a clean boundary here.
# ============================================================

from dataclasses import dataclass, field
import random


@dataclass
class PipelineResult:
    """
    The structured output of a CV pipeline run.

    The real pipeline will fill these same fields from actual video:
      - landing_frame: index of the frame where the athlete lands
      - measurements: raw biomechanical numbers (degrees / percent)
      - landmark_count: how many pose landmarks were tracked (33 for MediaPipe)
    """
    landing_frame: int
    measurements: dict[str, float]
    landmark_count: int = 33
    notes: list[str] = field(default_factory=list)


# The measurements every pipeline (mock or real) must produce.
# Keeping this list in one place documents the contract.
MEASUREMENT_KEYS = [
    "knee_flexion",   # degrees of knee bend at landing
    "knee_valgus",    # degrees of inward knee collapse
    "trunk_lean",     # degrees of torso tilt
    "asymmetry",      # percent difference between left and right sides
    "hip_flexion",    # degrees of hip bend at landing
]


def run_pipeline(seed: str, video_path: str | None = None) -> PipelineResult:
    """
    Produce a PipelineResult for a video.

    MOCK BEHAVIOR: we don't actually open the video. We seed a random
    generator with `seed` (the upload id) so the same upload always yields
    the same numbers — stable for demos — while different uploads differ.

    REAL BEHAVIOR (Stage 7): this function will open video_path, run
    MediaPipe Pose frame by frame, detect the landing frame, and compute
    these measurements from the landmark coordinates. The RETURN TYPE
    stays identical, so nothing downstream changes.
    """
    rng = random.Random(seed)

    measurements = {
        "knee_flexion": round(rng.uniform(55, 95), 1),
        "knee_valgus": round(rng.uniform(3, 20), 1),
        "trunk_lean": round(rng.uniform(2, 18), 1),
        "asymmetry": round(rng.uniform(2, 22), 1),
        "hip_flexion": round(rng.uniform(40, 90), 1),
    }

    # A pretend landing-frame index (real version detects this from motion).
    landing_frame = rng.randint(20, 60)

    return PipelineResult(
        landing_frame=landing_frame,
        measurements=measurements,
        landmark_count=33,
        notes=["Mock pipeline: values are simulated, not measured from video."],
    )
