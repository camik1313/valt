# ============================================================
# storage.py — reads and writes data to disk.
#
# Right now "the database" is just JSON files in backend/data/.
# That's perfectly fine for a project at this stage. Crucially,
# EVERY other file talks to storage through these functions — so
# the day we upgrade to a real database (Postgres, etc.), we only
# rewrite THIS file. Nothing else changes. That's the payoff of
# putting storage behind a service.
# ============================================================

import json
import os
import uuid
from datetime import datetime

from app.config import settings
from app.models.schemas import Analysis, HistoryItem


def _ensure_dirs() -> None:
    """Make sure the upload and analyses folders exist before we use them."""
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.analyses_dir, exist_ok=True)


def save_upload(file_bytes: bytes, original_filename: str) -> tuple[str, str]:
    """
    Save an uploaded video to disk.

    Returns (upload_id, saved_path). The upload_id is a random unique
    string so two files named "jump.mp4" never collide.
    """
    _ensure_dirs()
    upload_id = uuid.uuid4().hex[:12]  # e.g. "9f2a7c1b4e6d"

    # Keep the original extension (.mp4, .mov) so the file stays playable.
    ext = os.path.splitext(original_filename)[1] or ".mp4"
    saved_path = os.path.join(settings.upload_dir, f"{upload_id}{ext}")

    with open(saved_path, "wb") as f:  # "wb" = write bytes
        f.write(file_bytes)

    return upload_id, saved_path


def save_analysis(analysis: Analysis) -> None:
    """Write one analysis result to its own JSON file, named by its id."""
    _ensure_dirs()
    path = os.path.join(settings.analyses_dir, f"{analysis.id}.json")
    with open(path, "w") as f:
        # by_alias=True writes camelCase keys, matching what we send the frontend.
        json.dump(analysis.model_dump(by_alias=True), f, indent=2)


def get_analysis(analysis_id: str) -> Analysis | None:
    """Load one analysis by id, or return None if it doesn't exist."""
    path = os.path.join(settings.analyses_dir, f"{analysis_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        data = json.load(f)
    # Rebuild a validated Analysis object from the stored JSON.
    return Analysis.model_validate(data)


def list_analyses() -> list[HistoryItem]:
    """List all saved analyses, newest first, as short history entries."""
    _ensure_dirs()
    items: list[HistoryItem] = []

    for filename in os.listdir(settings.analyses_dir):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(settings.analyses_dir, filename), "r") as f:
            data = json.load(f)
        items.append(
            HistoryItem(
                id=data["id"],
                athlete_name=data["athleteName"],
                created_at=data["createdAt"],
                summary=data["summary"],
            )
        )

    # Sort newest-first by the timestamp string (ISO sorts correctly as text).
    items.sort(key=lambda it: it.created_at, reverse=True)
    return items


def new_analysis_id() -> str:
    """A fresh unique id for a new analysis."""
    return uuid.uuid4().hex[:12]


def now_iso() -> str:
    """Current time as an ISO string, e.g. '2026-07-04T12:00:00'."""
    return datetime.now().isoformat(timespec="seconds")


def find_upload_path(upload_id: str) -> str | None:
    """
    Find the saved video file for an upload_id.

    We saved it as "<upload_id><ext>", but we don't know the extension
    up front, so we scan the upload folder for a matching prefix.
    Returns the full path, or None if not found.
    """
    _ensure_dirs()
    if not os.path.isdir(settings.upload_dir):
        return None
    for filename in os.listdir(settings.upload_dir):
        if filename.startswith(upload_id):
            return os.path.join(settings.upload_dir, filename)
    return None


def delete_video(path: str | None) -> None:
    """
    Remove a saved video from disk once it's no longer needed: after a
    successful analysis (the raw video isn't needed once we have the
    measurements), or immediately after a failed one (no reason to keep
    an unusable file around). Takes a resolved path rather than an
    upload_id since report_service already has both clips' paths on
    hand either way. Never raises if the path is missing or already gone.
    """
    if path and os.path.exists(path):
        os.remove(path)
