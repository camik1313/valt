# ============================================================
# report_service.py — turns a video into a finished Analysis.
#
# Division of labor (unchanged):
#   cv/pipeline    -> RAW measurements (the science)
#   report_service -> INTERPRETATION (banding, summary, assembling schema)
#
# VIEW-AWARE: the pipeline only returns measurements valid for the camera
# angle, so this file just labels and bands whatever it gets back. No
# averaging across legs — asymmetry is the point, and averaging hides it.
# ============================================================

from app.models.schemas import (
    Analysis,
    ContributingFactor,
    LessItemScore,
    LessQuestionnaireAnswers,
    LessScore,
    Metric,
    PartialScore,
    QuestionnaireAnswers,
    RiskScore,
)
from app.services import storage
from app.cv import pipeline, mock_pipeline
from app.risk import scoring as risk_scoring
from app.risk import less as less_scoring

# Set False to force the mock pipeline (instant, fake numbers).
USE_REAL_PIPELINE = True

# Human-friendly labels + units, keyed by measurement name.
LABELS = {
    # Frontal plane (front view)
    "knee_valgus_left": ("Knee valgus, left", "HW"),
    "knee_valgus_right": ("Knee valgus, right", "HW"),
    "valgus_asymmetry": ("Valgus asymmetry", "%"),
    "kasr": ("Knee/ankle separation", "ratio"),
    "trunk_lean_lateral": ("Trunk lean (lateral)", "deg"),
    # Sagittal plane (side view)
    "knee_flexion_left": ("Knee flexion, left", "deg"),
    "knee_flexion_right": ("Knee flexion, right", "deg"),
    "hip_flexion_left": ("Hip flexion, left", "deg"),
    "hip_flexion_right": ("Hip flexion, right", "deg"),
    "flexion_asymmetry": ("Flexion asymmetry", "%"),
    "trunk_lean_forward": ("Trunk lean (forward)", "deg"),
    # Mock-only keys (fallback path)
    "knee_flexion": ("Knee flexion", "deg"),
    "knee_valgus": ("Dynamic knee valgus", "deg"),
    "trunk_lean": ("Trunk lean", "deg"),
    "asymmetry": ("Left / right asymmetry", "%"),
    "hip_flexion": ("Hip flexion", "deg"),
}

# Display order. We show whatever exists, in this order.
DISPLAY_ORDER = [
    "knee_valgus_left", "knee_valgus_right", "valgus_asymmetry", "kasr", "trunk_lean_lateral",
    "knee_flexion_left", "knee_flexion_right", "flexion_asymmetry",
    "hip_flexion_left", "hip_flexion_right", "trunk_lean_forward",
    "knee_flexion", "knee_valgus", "trunk_lean", "asymmetry", "hip_flexion",
]

# ILLUSTRATIVE banding thresholds (watch_at, flag_at) applied to the
# ABSOLUTE value. PLACEHOLDERS — Part 5 replaces these with values cited
# from ACL injury-prevention literature.
THRESHOLDS = {
    "knee_valgus_left": (0.15, 0.25),
    "knee_valgus_right": (0.15, 0.25),
    "knee_valgus": (10, 15),
    "trunk_lean_lateral": (10, 15),
    "trunk_lean_forward": (30, 45),
    "trunk_lean": (10, 15),
    "valgus_asymmetry": (25, 50),
    "flexion_asymmetry": (10, 15),
    "asymmetry": (10, 15),
}


def _to_scoring_answers(
    questionnaire: QuestionnaireAnswers | None,
) -> risk_scoring.QuestionnaireAnswers | None:
    """Convert the wire-facing (Pydantic) questionnaire into the plain
    dataclass risk/scoring.py works with, so scoring stays framework-free."""
    if questionnaire is None:
        return None
    return risk_scoring.QuestionnaireAnswers(
        previous_acl_injury=questionnaire.previous_acl_injury,
        sex=questionnaire.sex,
        sport_type=questionnaire.sport_type,
        age=questionnaire.age,
        activity_level=questionnaire.activity_level,
        fatigue_reported=questionnaire.fatigue_reported,
        previous_lower_limb_injury=questionnaire.previous_lower_limb_injury,
    )


def _to_risk_score_schema(result: risk_scoring.ScreeningResult) -> RiskScore:
    """Convert risk/scoring.py's plain-dataclass result into the Pydantic
    schema that goes out over the wire (camelCase, via CamelModel)."""

    def factors(fs: list[risk_scoring.ContributingFactor]) -> list[ContributingFactor]:
        return [
            ContributingFactor(key=f.key, label=f.label, points=f.points, detail=f.detail)
            for f in fs
        ]

    questionnaire_score = None
    if result.questionnaire is not None:
        questionnaire_score = PartialScore(
            points=result.questionnaire.points,
            max_points=result.questionnaire.max_points,
            factors=factors(result.questionnaire.factors),
        )

    return RiskScore(
        band=result.band,
        percent_of_max=result.percent_of_max,
        total_points=result.total_points,
        total_max_points=result.total_max_points,
        biomechanical=PartialScore(
            points=result.biomechanical.points,
            max_points=result.biomechanical.max_points,
            factors=factors(result.biomechanical.factors),
        ),
        questionnaire=questionnaire_score,
        factors=factors(result.factors),
        disclaimer=result.disclaimer,
    )


def _to_less_questionnaire_answers(
    answers: LessQuestionnaireAnswers | None,
) -> less_scoring.LessQuestionnaireAnswers | None:
    """Convert the wire-facing (Pydantic) LESS questionnaire into the plain
    dataclass risk/less.py works with, so scoring stays framework-free."""
    if answers is None:
        return None
    return less_scoring.LessQuestionnaireAnswers(
        foot_ir_max_flexion=answers.foot_ir_max_flexion,
        foot_er_max_flexion=answers.foot_er_max_flexion,
        overall_impression=answers.overall_impression,
    )


def _to_less_score_schema(result: less_scoring.LessResult) -> LessScore:
    """Convert risk/less.py's plain-dataclass result into the Pydantic
    schema that goes out over the wire (camelCase, via CamelModel)."""
    return LessScore(
        total_points=result.total_points,
        max_points=result.max_points,
        percent_of_max=result.percent_of_max,
        band=result.band,
        items=[
            LessItemScore(
                number=i.number, key=i.key, view=i.view, label=i.label,
                good_criterion=i.good_criterion, points=i.points,
                max_points=i.max_points, source=i.source, detail=i.detail,
            )
            for i in result.items
        ],
        views_available=result.views_available,
        disclaimer=result.disclaimer,
        cutoff_citation=result.cutoff_citation,
    )


def _band(key: str, value: float) -> str:
    """Convert a raw measurement into ok / watch / flag."""
    # Flexion is inverted: LOW flexion (a stiff landing) is the concern.
    if key.startswith("knee_flexion") or key.startswith("hip_flexion"):
        deficit = 70 - value  # degrees under a ~70 deg soft landing
        if deficit >= 15:
            return "flag"
        if deficit >= 8:
            return "watch"
        return "ok"

    if key in THRESHOLDS:
        watch_at, flag_at = THRESHOLDS[key]
        # Valgus is signed: negative = varus. We band on MAGNITUDE, since
        # deviation in either direction is worth noticing.
        v = abs(value)
        if v >= flag_at:
            return "flag"
        if v >= watch_at:
            return "watch"
        return "ok"

    return "ok"


def _build_summary(
    athlete_name: str,
    used_mock: bool,
    fallback_reason: str,
    metrics_list: list[Metric],
    less_result: less_scoring.LessResult | None,
    notes: list[str],
) -> str:
    """
    Build the plain-language report summary as a few short, distinct
    paragraphs (joined with blank lines) rather than one long run-on
    sentence — a headline finding in plain language, then the specific
    measurements and LESS items behind it in precise terms, then the
    disclaimer, then a technical footnote. Frontend renders the blank
    lines as paragraph breaks (whitespace-pre-line).
    """
    if used_mock:
        return (
            f"SIMULATED RESULT for {athlete_name}. The video could not be analyzed "
            f"({fallback_reason}), so these numbers are placeholders, not "
            f"measurements. Re-film with the whole body in frame and try again."
        )

    flags = [m.label for m in metrics_list if m.status == "flag"]
    watches = [m.label for m in metrics_list if m.status == "watch"]
    less_flagged = [i.label for i in less_result.items if i.points > 0] if less_result else []

    # ---- Headline: one plain-language sentence ----
    if less_result is not None and less_result.band == "high":
        headline = (
            f"{athlete_name}'s landing showed several movement patterns that "
            f"research literature associates with higher ACL injury risk."
        )
    elif flags or (less_result is not None and less_result.band == "moderate"):
        headline = (
            f"{athlete_name}'s landing showed a few movement patterns worth a "
            f"closer look, alongside others that looked typical."
        )
    elif watches or less_flagged:
        headline = (
            f"{athlete_name}'s landing mostly looked typical, with a couple of "
            f"borderline measurements."
        )
    else:
        headline = f"{athlete_name}'s landing looked mechanically typical across every measurement taken."

    paragraphs = [headline]

    # ---- Specific findings, in precise/professional language ----
    detail_bits = []
    if flags:
        detail_bits.append(f"On the individual measurements: {', '.join(flags)} were notable.")
    elif watches:
        detail_bits.append(f"On the individual measurements: {', '.join(watches)} sat near the borderline.")

    if less_result is not None and less_result.max_points > 0:
        if less_flagged:
            detail_bits.append(
                f"On the Landing Error Scoring System (LESS), a validated "
                f"17-item clinical movement-quality checklist, this landing "
                f"scored {less_result.total_points:g} of {less_result.max_points:g} "
                f"possible points for this session ({less_result.band}-band), "
                f"flagging: {', '.join(less_flagged)}."
            )
        else:
            detail_bits.append(
                f"On the Landing Error Scoring System (LESS), this landing "
                f"scored {less_result.total_points:g} of {less_result.max_points:g} "
                f"possible points for this session ({less_result.band}-band), "
                f"and no items were flagged."
            )

    if detail_bits:
        paragraphs.append(" ".join(detail_bits))

    paragraphs.append(
        "These are movement observations from an automated screening tool, "
        "not a medical diagnosis."
    )

    if notes:
        paragraphs.append("Technical notes: " + " ".join(notes))

    return "\n\n".join(paragraphs)


def build_analysis(
    upload_id: str,
    athlete_name: str,
    video_filename: str,
    video_path: str | None = None,
    view: str = "front",
    questionnaire: QuestionnaireAnswers | None = None,
    less_questionnaire: LessQuestionnaireAnswers | None = None,
    side_video_path: str | None = None,
    side_video_filename: str | None = None,
) -> Analysis:
    """
    Run the pipeline on a video and assemble a full Analysis.

    Falls back to the mock if the PRIMARY clip's real pipeline fails,
    clearly labeled so simulated numbers can never be mistaken for
    measurements.

    Optionally accepts a SECOND clip from the same session, filmed from the
    opposite camera angle (see AnalyzeRequest.side_upload_id). When given
    and the primary clip was real, its measurements are merged in — this is
    what lets both the screening score and the LESS score see both frontal-
    and sagittal-plane criteria instead of just one (LESS in particular
    needs both views for all 15 numeric items — see risk/less.py). The
    second clip is a bonus, not a requirement: if it fails to analyze, we
    keep the primary clip's real measurements and just note that the
    second angle is missing, rather than discarding a real result.
    """
    used_mock = False
    fallback_reason = ""

    # ---- 1) Primary clip ----
    if USE_REAL_PIPELINE and video_path:
        try:
            result = pipeline.run_pipeline(seed=upload_id, video_path=video_path, view=view)
        except Exception as exc:
            result = mock_pipeline.run_pipeline(seed=upload_id)
            used_mock = True
            fallback_reason = str(exc)
    else:
        result = mock_pipeline.run_pipeline(seed=upload_id)
        used_mock = True
        fallback_reason = "Real pipeline disabled."

    measurements: dict[str, float] = dict(result.measurements)
    less_raw: dict[str, float] = dict(getattr(result, "less_raw", {}) or {})
    notes: list[str] = list(result.notes)
    views_used = [view]

    # ---- 2) Optional second clip, opposite angle, same session ----
    if not used_mock and side_video_path:
        side_view = "side" if view == "front" else "front"
        try:
            side_result = pipeline.run_pipeline(
                seed=f"{upload_id}-side", video_path=side_video_path, view=side_view
            )
            measurements.update(side_result.measurements)
            less_raw.update(getattr(side_result, "less_raw", {}) or {})
            notes.extend(side_result.notes)
            views_used.append(side_view)
        except Exception as exc:
            notes.append(
                f"The {side_view}-view clip from this session couldn't be analyzed "
                f"({exc}), so only {view}-view measurements are included below."
            )

    # ---- 3) Label and band ----
    metrics_list: list[Metric] = []
    for key in DISPLAY_ORDER:
        if key not in measurements:
            continue
        value = measurements[key]
        label, unit = LABELS.get(key, (key, ""))
        metrics_list.append(
            Metric(key=key, label=label, value=value, unit=unit, status=_band(key, value))
        )

    # ---- 4) Screening risk score (epidemiological + illustrative subset) ----
    # Only computed when the real pipeline actually produced measurements.
    # A mock fallback has no real biomechanics to screen, so we don't
    # fabricate a score off placeholder numbers — see risk/scoring.py.
    risk_score = None
    if not used_mock:
        screening = risk_scoring.compute_screening_score(
            measurements, _to_scoring_answers(questionnaire)
        )
        risk_score = _to_risk_score_schema(screening)

    # ---- 5) LESS score (the real, cited 17-item assessment) ----
    # See risk/less.py. Uses less_raw (initial-contact + max-flexion frame
    # data), merged across both clips exactly like `measurements` above.
    less_result = None
    less_score_schema = None
    if not used_mock:
        less_result = less_scoring.compute_less_score(
            less_raw, _to_less_questionnaire_answers(less_questionnaire)
        )
        less_score_schema = _to_less_score_schema(less_result)

    # ---- 6) Summary ----
    view_label = "+".join(views_used)
    summary = _build_summary(athlete_name, used_mock, fallback_reason, metrics_list, less_result, notes)

    # ---- 7) Assemble ----
    combined_filename = video_filename
    if side_video_filename:
        combined_filename = f"{video_filename} + {side_video_filename}"

    return Analysis(
        id=storage.new_analysis_id(),
        athlete_name=athlete_name,
        created_at=storage.now_iso(),
        video_filename=combined_filename,
        view=view_label,
        metrics=metrics_list,
        summary=summary,
        risk_score=risk_score,
        less_score=less_score_schema,
    )
