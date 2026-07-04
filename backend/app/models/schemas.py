# ============================================================
# schemas.py — the DATA CONTRACT between backend and frontend.
#
# Each class below is a "schema": a precise description of what a
# piece of data looks like. FastAPI uses these to (a) validate
# incoming requests and (b) shape outgoing responses. If the
# frontend sends the wrong shape, FastAPI rejects it automatically.
#
# NAMING NOTE: Python code uses snake_case (athlete_name), but
# JavaScript/JSON prefers camelCase (athleteName). We bridge that
# with an alias generator so the JSON on the wire is camelCase —
# matching frontend/src/lib/types.ts exactly — while our Python
# code stays Pythonic. Best of both worlds.
# ============================================================

from typing import Literal
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base class: every schema inherits camelCase JSON output."""
    model_config = ConfigDict(
        alias_generator=to_camel,   # athlete_name -> athleteName in JSON
        populate_by_name=True,      # still accept snake_case when constructing in Python
    )


# ---- One measured biomechanical value ----
class Metric(CamelModel):
    key: str        # machine name, e.g. "knee_flexion"
    label: str      # human name, e.g. "Knee flexion"
    value: float    # the measured number
    unit: str       # e.g. "deg" or "%"
    # research-informed banding: ok = looks fine, watch = borderline, flag = notable
    status: Literal["ok", "watch", "flag"]


# ---- A complete analysis of one video ----
class Analysis(CamelModel):
    id: str
    athlete_name: str
    created_at: str          # ISO timestamp, e.g. "2026-07-04T12:00:00"
    video_filename: str
    metrics: list[Metric]
    summary: str             # plain-language overview


# ---- Response after uploading a video ----
class UploadResponse(CamelModel):
    upload_id: str
    filename: str
    message: str


# ---- Request body for starting an analysis ----
class AnalyzeRequest(CamelModel):
    upload_id: str
    athlete_name: str = "Athlete"   # optional; defaults if not provided


# ---- A short entry for the history list ----
class HistoryItem(CamelModel):
    id: str
    athlete_name: str
    created_at: str
    summary: str
