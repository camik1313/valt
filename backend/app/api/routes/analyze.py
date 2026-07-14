# ============================================================
# analyze.py — the POST /analyze endpoint.
#
# Takes an upload_id (from /upload) plus an athlete name, finds the
# saved video on disk, runs the analysis, saves it, and returns it.
#
# STAGE 7: now looks up the real video path so the CV pipeline has
# an actual file to analyze. The route stays thin — it does HTTP and
# delegates the work to the service.
# ============================================================

from fastapi import APIRouter, HTTPException

from app.models.schemas import Analysis, AnalyzeRequest
from app.services import report_service, storage

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=Analysis)
async def analyze_video(request: AnalyzeRequest):
    # Find the video that was uploaded earlier.
    video_path = storage.find_upload_path(request.upload_id)
    if video_path is None:
        raise HTTPException(
            status_code=404,
            detail="That upload could not be found. Please upload the video again.",
        )

    # Build the analysis (runs the real CV pipeline).
    analysis = report_service.build_analysis(
        upload_id=request.upload_id,
        athlete_name=request.athlete_name,
        video_filename=video_path.split("/")[-1],
        video_path=video_path,
        view=request.view,
    )

    # Persist it so it appears in history and can be reopened by id.
    storage.save_analysis(analysis)

    return analysis
