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

    # A second, opposite-angle clip from the same session is optional.
    # If given but not found, we don't fail the whole request — the
    # primary clip alone is still a complete analysis.
    side_video_path = None
    side_video_filename = None
    if request.side_upload_id:
        side_video_path = storage.find_upload_path(request.side_upload_id)
        if side_video_path:
            side_video_filename = side_video_path.split("/")[-1]

    # Build the analysis (runs the real CV pipeline). A failure on the
    # PRIMARY clip (bad video, no body detected, wrong orientation, too
    # long, etc.) now raises instead of silently returning fabricated
    # numbers — surface that specific reason so the athlete gets a real
    # error message and can retry, not a 500 or a fake result.
    try:
        analysis = report_service.build_analysis(
            upload_id=request.upload_id,
            athlete_name=request.athlete_name,
            video_filename=video_path.split("/")[-1],
            video_path=video_path,
            view=request.view,
            questionnaire=request.questionnaire,
            less_questionnaire=request.less_questionnaire,
            side_video_path=side_video_path,
            side_video_filename=side_video_filename,
            athlete_height_cm=request.athlete_height_cm,
            ground_window_seconds=request.ground_window_seconds,
            box_window_seconds=request.box_window_seconds,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Persist it so it appears in history and can be reopened by id.
    storage.save_analysis(analysis)

    return analysis
