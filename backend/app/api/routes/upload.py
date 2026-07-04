# ============================================================
# upload.py — the POST /upload endpoint.
#
# Receives a video file from the browser, validates it's a video,
# saves it, and returns an upload_id the frontend uses next.
#
# NOTE how thin this is: the route only handles the HTTP concerns
# (receiving the file, returning a response). The actual saving is
# delegated to the storage service. Routes stay thin; services do work.
# ============================================================

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.models.schemas import UploadResponse
from app.services import storage

# A router groups related endpoints. main.py wires it into the app.
router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...)):
    # Basic validation: content_type looks like "video/mp4", "video/quicktime"...
    if not file.content_type or not file.content_type.startswith("video/"):
        # 400 = "Bad Request": the client sent something we can't accept.
        raise HTTPException(status_code=400, detail="Uploaded file must be a video.")

    # Read the file's bytes and hand them to storage.
    file_bytes = await file.read()
    upload_id, _saved_path = storage.save_upload(file_bytes, file.filename or "video.mp4")

    return UploadResponse(
        upload_id=upload_id,
        filename=file.filename or "video.mp4",
        message="Upload received.",
    )
