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


# ============================================================
# SCREENING RISK SCORE — see backend/app/risk/scoring.py for the full
# explanation of what this is (and, just as important, what it is NOT:
# not a diagnosis, not a trained model, not an injury probability, not
# a reimplementation of the full LESS). These schemas just carry that
# module's result shape over the wire; the scoring itself lives there.
# ============================================================

# ---- Optional self-report questionnaire (every field optional) ----
Sex = Literal["female", "male", "other", "prefer_not_to_say"]
SportType = Literal["pivoting_cutting", "field_court_other", "endurance_noncontact", "other"]
ActivityLevel = Literal["sedentary", "recreational", "competitive_high_school", "competitive_college_or_pro"]


class QuestionnaireAnswers(CamelModel):
    previous_acl_injury: bool | None = None
    sex: Sex | None = None
    sport_type: SportType | None = None
    age: int | None = None
    activity_level: ActivityLevel | None = None
    fatigue_reported: bool | None = None
    previous_lower_limb_injury: bool | None = None


# ---- One factor that moved the screening score, in plain language ----
class ContributingFactor(CamelModel):
    key: str
    label: str
    points: float
    detail: str


# ---- Subtotal for one half of the score (biomechanical or questionnaire) ----
class PartialScore(CamelModel):
    points: float
    max_points: float
    factors: list[ContributingFactor]


# ---- The full screening result attached to an Analysis ----
class RiskScore(CamelModel):
    band: Literal["low", "moderate", "elevated"]
    percent_of_max: float     # 0..100, percent of ACHIEVABLE points — not a probability
    total_points: float
    total_max_points: float
    biomechanical: PartialScore
    # None when no questionnaire was submitted — the frontend then shows
    # the biomechanical portion only, per the product requirement.
    questionnaire: PartialScore | None = None
    factors: list[ContributingFactor]   # biomechanical + questionnaire, combined
    disclaimer: str


# ---- A complete analysis of one video ----
class Analysis(CamelModel):
    id: str
    athlete_name: str
    created_at: str          # ISO timestamp, e.g. "2026-07-04T12:00:00"
    video_filename: str
    # "front", "side", or "front+side" / "side+front" when a same-session
    # second clip from the opposite angle was combined into this analysis.
    view: str = "front"
    metrics: list[Metric]
    summary: str             # plain-language overview
    # None when the real pipeline didn't run (e.g. mock fallback) — there are
    # no real measurements to screen in that case, so we don't fabricate one.
    risk_score: RiskScore | None = None


# ---- Response after uploading a video ----
class UploadResponse(CamelModel):
    upload_id: str
    filename: str
    message: str


# ---- Request body for starting an analysis ----
class AnalyzeRequest(CamelModel):
    upload_id: str
    athlete_name: str = "Athlete"   # optional; defaults if not provided
    # Which camera angle the PRIMARY video was filmed from. This determines
    # which measurements are scientifically valid (see cv/pipeline.py).
    view: str = "front"
    # Optional second clip from the SAME session, filmed from the opposite
    # angle (front primary -> side second, or vice versa). When present,
    # its measurements are merged with the primary clip's, giving the
    # screening score access to both frontal- and sagittal-plane criteria
    # instead of just one. Omit to analyze a single clip as before.
    side_upload_id: str | None = None
    # Optional screening questionnaire. Omit entirely (or send null) to skip
    # it — the resulting risk score then reports the biomechanical portion only.
    questionnaire: QuestionnaireAnswers | None = None


# ---- A short entry for the history list ----
class HistoryItem(CamelModel):
    id: str
    athlete_name: str
    created_at: str
    summary: str
