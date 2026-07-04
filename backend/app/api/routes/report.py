# ============================================================
# report.py — the GET /report/{analysis_id} endpoint.
#
# Fetches a single saved analysis by its id. If no analysis with
# that id exists, returns a 404 (Not Found).
# ============================================================

from fastapi import APIRouter, HTTPException

from app.models.schemas import Analysis
from app.services import storage

router = APIRouter(tags=["report"])


@router.get("/report/{analysis_id}", response_model=Analysis)
async def get_report(analysis_id: str):
    analysis = storage.get_analysis(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return analysis
