# ============================================================
# analyze.py — the POST /analyze endpoint.
#
# Takes an upload_id (from /upload) plus an athlete name, builds an
# Analysis via the report service, saves it, and returns it.
#
# The route stays thin: it does HTTP, then delegates to the service.
# ============================================================

from fastapi import APIRouter

from app.models.schemas import Analysis, AnalyzeRequest
from app.services import report_service, storage

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=Analysis)
async def analyze_video(request: AnalyzeRequest):
    # Build the analysis. We pass the upload id as the filename for now;
    # in a later stage we'll look up the real saved filename.
    analysis = report_service.build_analysis(
        upload_id=request.upload_id,
        athlete_name=request.athlete_name,
        video_filename=f"{request.upload_id}.mp4",
    )

    # Persist it so it appears in history and can be reopened by id.
    storage.save_analysis(analysis)

    return analysis
