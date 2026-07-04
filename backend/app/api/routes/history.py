# ============================================================
# history.py — the GET /history endpoint.
#
# Returns a list of all saved analyses (newest first) as short
# summary entries, for the history page to display.
# ============================================================

from fastapi import APIRouter

from app.models.schemas import HistoryItem
from app.services import storage

router = APIRouter(tags=["history"])


@router.get("/history", response_model=list[HistoryItem])
async def get_history():
    return storage.list_analyses()
