# ============================================================
# analyze.py — the POST /analyze endpoint.
#
# Takes an upload_id (from /upload) plus an athlete name, builds an
# Analysis (mock metrics for now), saves it, and returns it.
#
# When the real CV pipeline arrives, NONE of this changes — only
# the internals of report_service.build_analysis() do.
# ============================================================

from fastapi import APIRouter

from app.models.schemas import Analysis, AnalyzeRequest
from app.services import report_service, storage

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=Analysis)
async def analyze_video(request: AnalyzeRequest):
    # Build the analysis (mock for now).
    analysis = report_service.build_analysis(
        upload_id=request.upload_id,
        filename=f"{request.upload_id}",  # we only stored by id for now
        athlete_name=request.athlete_name,
    )

    # Persist it so it shows up in history and can be reopened by id.
    storage.save_analysis(analysis)

    return analysis
