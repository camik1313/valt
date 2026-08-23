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
    # When True, exercise recommendations are withheld entirely (see
    # ExerciseRecommendations.gated_reason below) — an active injury is a
    # reason to see a clinician, not a reason to get a workout suggestion
    # from a screening app.
    current_pain_or_injury: bool | None = None


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


# ============================================================
# LESS (Landing Error Scoring System) — see backend/app/risk/less.py
# for the full explanation, citations, and every threshold's source.
# This is the REAL, cited 17-item LESS, not an inspired subset.
# ============================================================

OverallImpression = Literal["excellent", "average", "poor"]


# ---- The 3 items no 2D camera can score (self-reported) ----
class LessQuestionnaireAnswers(CamelModel):
    foot_ir_max_flexion: bool | None = None   # item 13: toes turned in >30° at max flexion?
    foot_er_max_flexion: bool | None = None   # item 14: toes turned out >30° at max flexion?
    overall_impression: OverallImpression | None = None  # item 17


# ---- One of the 17 LESS items, scored ----
class LessItemScore(CamelModel):
    number: int              # 1-17, matching the official scoring sheet
    key: str
    view: Literal["sagittal", "frontal", "overall"]
    label: str                # the official sheet's short name
    good_criterion: str       # the official sheet's "no error" description
    points: int
    max_points: int
    source: Literal["measured", "self_reported", "unavailable"]
    detail: str                # plain-language explanation of this item's score


# ---- The full LESS result attached to an Analysis ----
class LessScore(CamelModel):
    total_points: float
    max_points: float          # only items THIS session could score count
    percent_of_max: float
    band: Literal["low", "moderate", "high"]
    items: list[LessItemScore]
    views_available: list[str]   # which of "front"/"side" contributed
    disclaimer: str
    cutoff_citation: str


# ============================================================
# PROTOCOL CHECK — see backend/app/cv/calibration.py. NOT a score: this is
# a measured record of whether the real LESS box-jump setup (12in/31cm
# box, land at half the athlete's height) was actually followed, derived
# from the athlete's own body in the video rather than a manually-entered
# box height. None whenever calibration wasn't attempted or confident.
# ============================================================
class ProtocolCheck(CamelModel):
    box_height_cm: float | None = None
    landing_distance_cm: float | None = None
    landing_distance_target_cm: float | None = None
    landing_distance_delta_cm: float | None = None
    confident: bool = False
    note: str = ""


# ============================================================
# EXERCISE RECOMMENDATIONS — see backend/app/exercises/priorities.py
# (what's flagged) and ranking.py (what's recommended for it). Every
# exercise traces to a real, cited injury-prevention program; see
# exercises/research_library.py and exercises/database.py.
# ============================================================

class MovementPriority(CamelModel):
    target: str            # e.g. "frontal_knee_control"
    target_label: str       # e.g. "frontal knee control"
    severity: float          # 0..1
    evidence: list[str]


# ---- One exercise from the library, no personalization applied ----
class ExerciseInfo(CamelModel):
    exercise_id: str
    exercise_name: str
    short_description: str
    instructions: list[str]
    movement_targets: list[str]
    difficulty: Literal["beginner", "intermediate", "advanced"]
    equipment: str
    age_ranges: list[str]
    sports: list[str]
    competitive_levels: list[str]
    research_source: str
    source_program: str
    safety_notes: str


# ---- One exercise as ranked against a specific athlete's scan ----
class RecommendedExercise(ExerciseInfo):
    score: float
    matched_targets: list[str]
    why: str


# ---- The full recommendation result attached to an Analysis ----
class ExerciseRecommendations(CamelModel):
    # Non-None means recommendations were deliberately withheld, and why
    # (see report_service.py) — e.g. the athlete reported current pain or
    # injury. Distinct from "computed, and nothing was flagged," which
    # returns gated_reason=None with empty lists.
    gated_reason: str | None = None
    priorities: list[MovementPriority]
    exercises: list[RecommendedExercise]
    disclaimer: str


# ============================================================
# LANDING PROFILE — see backend/app/reports/landing_profile.py. The
# simple, always-four-categories summary shown before the technical
# LESS/metric breakdown, and what Compare (below) diffs between two
# analyses.
# ============================================================

class LandingProfileCategory(CamelModel):
    category: str            # e.g. "knee_control"
    label: str                 # e.g. "Knee control"
    rating: Literal["ok", "watch", "flag", "unavailable"]
    value: float | None = None
    unit: str | None = None
    metric_label: str | None = None
    explanation: str
    source_view: str | None = None


class LandingProfile(CamelModel):
    categories: list[LandingProfileCategory]


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
    # The real, cited LESS score (see risk/less.py). Also None on mock fallback.
    less_score: LessScore | None = None
    # Measured box-jump protocol fidelity. None when calibration wasn't
    # available for this analysis (see ProtocolCheck above).
    protocol_check: ProtocolCheck | None = None
    # Personalized exercise recommendations from this scan's movement
    # priorities (see exercises/priorities.py, ranking.py). None when
    # there's no real questionnaire/measurements to rank against (mock
    # fallback, or no questionnaire submitted) — distinct from a real,
    # computed ExerciseRecommendations with an empty exercise list.
    recommendations: ExerciseRecommendations | None = None
    # The simple, always-four-category summary (see LandingProfile above).
    # None only on mock fallback — unlike recommendations, this doesn't
    # need a questionnaire, so it's computed whenever real measurements
    # exist.
    landing_profile: LandingProfile | None = None


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
    # Optional answers to the 3 LESS items no camera can score (foot
    # rotation x2, overall impression). Omit to skip — those 3 items just
    # won't count toward the LESS total.
    less_questionnaire: LessQuestionnaireAnswers | None = None
    # Optional box-jump protocol calibration (see cv/calibration.py). Only
    # meaningful for the guided box-jump capture flow, which knows exactly
    # when the athlete was standing on the ground vs. on the box; the plain
    # upload fallback has no such choreography and should omit all three.
    # All three must be present together to attempt calibration.
    athlete_height_cm: float | None = None
    ground_window_seconds: tuple[float, float] | None = None
    box_window_seconds: tuple[float, float] | None = None


# ---- A short entry for the history list ----
class HistoryItem(CamelModel):
    id: str
    athlete_name: str
    created_at: str
    summary: str
