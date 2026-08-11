# ============================================================
# risk/scoring.py — SCREENING RISK SCORE.
#
# WHAT THIS IS: a transparent, points-based screening score built from
# (a) the biomechanical measurements the CV pipeline already produces and
# (b) a short self-report questionnaire. Every number that goes into the
# score is visible below, with a comment on where it came from.
#
# WHAT THIS IS NOT, EVER:
#   - NOT a diagnosis. It does not detect ACL injury or any pathology.
#   - NOT a trained model. There is no dataset, no fitting, no learned
#     weights. Every weight and threshold below is a value someone chose
#     by hand, informed by published injury-prevention literature, and
#     is meant to be inspected and adjusted, not trusted as ground truth.
#   - NOT a predictor. This module never computes or reports an injury
#     probability. It reports a points total and a qualitative band
#     ("low" / "moderate" / "elevated") plus which factors moved the
#     score — nothing more, on purpose.
#   - NOT full LESS. The Landing Error Scoring System (Padua et al. 2009,
#     "The Landing Error Scoring System (LESS) Is a Valid and Reliable
#     Clinical Assessment Tool of Jump-Landing Biomechanics") scores 17
#     items from a two-camera (front + side) setup, several of which
#     need frame-by-frame trunk/knee tracking across the whole landing
#     phase. This app's 2D single-view pipeline can only ever measure a
#     SUBSET of those items, and only the ones valid for whichever view
#     (front or side) the clip was filmed from — see VALID_MEASUREMENTS
#     in cv/pipeline.py. We only score what we can actually see.
#
# TWO INDEPENDENT PARTS, always kept separate in the output:
#   1. Biomechanical error points — from BIOMECH_CRITERIA below, applied
#      to whichever measurements the pipeline produced for this clip's
#      view. A front-view clip can only ever trigger frontal-plane
#      criteria (valgus, lateral trunk lean); a side-view clip only
#      sagittal-plane ones (flexion, forward trunk lean). This mirrors
#      the pipeline's own view-aware design.
#   2. Questionnaire risk points — from QUESTIONNAIRE_CRITERIA below,
#      applied to self-reported answers. Entirely optional; if no
#      questionnaire is supplied, the result reports the biomechanical
#      portion only and questionnaire fields are left as None.
#
# HOW BANDING WORKS: each part has a maximum achievable point total
# (which varies by view / by which questionnaire fields were answered).
# We band on percent-of-achievable-max, NOT a raw point count, so a
# front-view clip (fewer possible criteria) isn't penalized relative to
# a side-view one. That percentage is a screening-score summary, not a
# probability of anything.
# ============================================================

from dataclasses import dataclass, field
from typing import Literal

Band = Literal["low", "moderate", "elevated"]

DISCLAIMER = (
    "This is a screening score, not a diagnosis. It is a transparent, "
    "literature-informed checklist covering only the biomechanical error "
    "criteria this app's 2D camera pipeline can actually measure — a "
    "small subset of the full 17-item Landing Error Scoring System (LESS), "
    "not a reimplementation of it. It is not a trained or validated "
    "predictive model, does not estimate an injury probability, and "
    "should never replace assessment by a qualified clinician."
)


# ============================================================
# PART 1 — BIOMECHANICAL ERROR CRITERIA (LESS-inspired subset)
#
# Each entry below is one screening criterion. `measurement` is the key
# in the pipeline's measurements dict (see cv/pipeline.py VALID_MEASUREMENTS)
# that the criterion reads. `direction` says which side of `threshold`
# counts as an error: "abs_ge" fires when |value| >= threshold (used for
# signed measurements where deviation either way matters), "lt" fires
# when value < threshold (used for "not enough of a good thing", e.g.
# insufficient flexion), "ge" fires when value >= threshold.
#
# Every threshold is illustrative and hand-chosen — NOT fit to data.
# Adjust freely; the whole point of this table is that it's inspectable.
# ============================================================

@dataclass(frozen=True)
class BiomechCriterion:
    key: str
    measurement: str            # key in the pipeline's measurements dict
    label: str
    direction: Literal["abs_ge", "lt", "ge"]
    threshold: float
    points: float
    unit: str
    citation: str


BIOMECH_CRITERIA: list[BiomechCriterion] = [
    # --- Frontal plane (front-view clips) ---
    BiomechCriterion(
        key="knee_valgus_left",
        measurement="knee_valgus_left",
        label="Left knee valgus at landing",
        direction="abs_ge",
        threshold=0.15,   # hip-widths; matches report_service's "watch" band
        points=2.0,
        unit="HW",
        citation=(
            "Illustrative threshold echoing LESS 'knee valgus at initial contact' "
            "/ 'at max knee flexion' items (Padua et al. 2009); loosely consistent "
            "with prospective dynamic-valgus screening (Hewett et al. 2005). "
            "Not derived from this app's own data."
        ),
    ),
    BiomechCriterion(
        key="knee_valgus_right",
        measurement="knee_valgus_right",
        label="Right knee valgus at landing",
        direction="abs_ge",
        threshold=0.15,
        points=2.0,
        unit="HW",
        citation="Same illustrative threshold as the left knee, mirrored.",
    ),
    BiomechCriterion(
        key="valgus_asymmetry",
        measurement="valgus_asymmetry",
        label="Left/right valgus asymmetry",
        direction="ge",
        threshold=25.0,   # percent; matches report_service's "watch" band
        points=1.5,
        unit="%",
        citation=(
            "Illustrative asymmetry cutoff, loosely modeled on limb-symmetry-index "
            "conventions used in return-to-sport literature (e.g. Paterno et al. "
            "2010 discusses <90% LSI as a flag); not a validated cutoff for valgus "
            "specifically."
        ),
    ),
    BiomechCriterion(
        key="trunk_lateral_lean",
        measurement="trunk_lean_lateral",
        label="Lateral trunk lean at landing",
        direction="ge",
        threshold=10.0,   # degrees
        points=1.5,
        unit="deg",
        citation=(
            "Illustrative threshold echoing LESS 'trunk lateral flexion at initial "
            "contact' item (Padua et al. 2009)."
        ),
    ),
    # --- Sagittal plane (side-view clips) ---
    BiomechCriterion(
        key="knee_flexion_left",
        measurement="knee_flexion_left",
        label="Insufficient left knee flexion (stiff landing)",
        direction="lt",
        threshold=55.0,   # degrees; below this reads as a stiff landing
        points=2.0,
        unit="deg",
        citation=(
            "Illustrative threshold: stiff, low-flexion landings raise estimated "
            "knee joint loading (Devita & Skelly 1992; Decker et al. 2003). LESS "
            "uses coarser ordinal bins for knee flexion at initial contact; this "
            "app reports a continuous angle instead, so the cutoff here is our own "
            "choice, not a LESS bin boundary."
        ),
    ),
    BiomechCriterion(
        key="knee_flexion_right",
        measurement="knee_flexion_right",
        label="Insufficient right knee flexion (stiff landing)",
        direction="lt",
        threshold=55.0,
        points=2.0,
        unit="deg",
        citation="Same illustrative threshold as the left knee, mirrored.",
    ),
    BiomechCriterion(
        key="flexion_asymmetry",
        measurement="flexion_asymmetry",
        label="Left/right knee flexion asymmetry",
        direction="ge",
        threshold=15.0,   # percent
        points=1.5,
        unit="%",
        citation="Illustrative asymmetry cutoff; see valgus_asymmetry note above.",
    ),
    BiomechCriterion(
        key="trunk_forward_flexion_deficit",
        measurement="trunk_lean_forward",
        label="Insufficient forward trunk flexion (stiff, upright landing)",
        direction="lt",
        threshold=20.0,   # degrees
        points=2.0,
        unit="deg",
        citation=(
            "Illustrative threshold echoing LESS 'trunk flexion at initial contact' "
            "item; an upright, extended-trunk landing pattern is associated with "
            "higher estimated ACL loading (Blackburn & Padua 2008)."
        ),
    ),
]


# ============================================================
# PART 2 — QUESTIONNAIRE RISK CRITERIA (self-reported, all optional)
# ============================================================

Sex = Literal["female", "male", "other", "prefer_not_to_say"]
SportType = Literal["pivoting_cutting", "field_court_other", "endurance_noncontact", "other"]
ActivityLevel = Literal["sedentary", "recreational", "competitive_high_school", "competitive_college_or_pro"]


@dataclass
class QuestionnaireAnswers:
    """Every field is optional; unanswered fields simply score 0 points."""
    previous_acl_injury: bool | None = None
    sex: Sex | None = None
    sport_type: SportType | None = None
    age: int | None = None
    activity_level: ActivityLevel | None = None
    fatigue_reported: bool | None = None
    previous_lower_limb_injury: bool | None = None


# --- Weights, each hand-chosen and cited. Not trained on any data. ---

PREVIOUS_ACL_INJURY_POINTS = 4.0
PREVIOUS_ACL_INJURY_CITATION = (
    "Illustrative weight — prior ACL injury is the single strongest known risk "
    "factor for a subsequent ACL injury (ipsilateral graft or contralateral); "
    "roughly 1 in 4 young athletes sustain a second ACL injury within 24 months "
    "of return to sport (Paterno et al. 2014; Wiggins et al. 2016 meta-analysis)."
)

FEMALE_SEX_POINTS = 2.0
FEMALE_SEX_CITATION = (
    "Illustrative weight — female athletes in pivoting/cutting sports show "
    "consistently higher non-contact ACL injury incidence than male athletes in "
    "the same sports in epidemiological studies (Prodromos et al. 2007 "
    "meta-analysis; Renstrom et al. 2008 IOC consensus statement). This reflects "
    "a population-level epidemiological pattern, not an individual prediction."
)

SPORT_TYPE_POINTS: dict[SportType, float] = {
    "pivoting_cutting": 2.0,     # e.g. soccer, basketball, handball, football
    "field_court_other": 1.0,    # other field/court sports with some change-of-direction
    "endurance_noncontact": 0.0,  # e.g. distance running, swimming, cycling
    "other": 0.0,
}
SPORT_TYPE_CITATION = (
    "Illustrative weights — pivoting/cutting sports carry substantially higher "
    "reported ACL injury rates than straight-line endurance sports (Agel et al. "
    "2005; Waldén et al. 2011)."
)

AGE_HIGH_INCIDENCE_MIN = 14
AGE_HIGH_INCIDENCE_MAX = 25
AGE_HIGH_INCIDENCE_POINTS = 1.0
AGE_CITATION = (
    "Illustrative weight — reported ACL injury incidence rises sharply in "
    "adolescence and stays elevated through the mid-20s in athletic populations "
    "(Beynnon et al. 2014; Shea et al. pediatric/adolescent incidence data), "
    "before declining. This is a population pattern, not an individual one."
)

COMPETITIVE_ACTIVITY_POINTS = 1.5
COMPETITIVE_ACTIVITY_CITATION = (
    "Illustrative weight — higher competitive exposure (more games/practices at "
    "a competitive level) means more at-risk landing/cutting exposures over time "
    "(Gornitzky et al. 2016 incidence-by-exposure analysis)."
)

FATIGUE_POINTS = 1.0
FATIGUE_CITATION = (
    "Illustrative weight — neuromuscular control of landing mechanics "
    "deteriorates under fatigue in laboratory studies (Chappell et al. 2005; "
    "Borotikar et al. 2008)."
)

PREVIOUS_LOWER_LIMB_INJURY_POINTS = 1.0
PREVIOUS_LOWER_LIMB_INJURY_CITATION = (
    "Illustrative weight — a prior lower-limb injury (e.g. ankle sprain) is a "
    "general marker of elevated future lower-limb injury risk in systematic "
    "reviews (Swart et al. 2014), independent of ACL-specific mechanisms."
)


# ============================================================
# RESULT SHAPES
# ============================================================

@dataclass
class ContributingFactor:
    key: str
    label: str
    points: float
    detail: str   # plain-language explanation, e.g. "0.28 HW >= 0.15 HW threshold"


@dataclass
class BiomechScore:
    points: float
    max_points: float
    factors: list[ContributingFactor]


@dataclass
class QuestionnaireScore:
    points: float
    max_points: float
    factors: list[ContributingFactor]


@dataclass
class ScreeningResult:
    band: Band
    percent_of_max: float          # 0..100, percent of ACHIEVABLE points — not a probability
    total_points: float
    total_max_points: float
    biomechanical: BiomechScore
    questionnaire: QuestionnaireScore | None   # None if no questionnaire was supplied
    factors: list[ContributingFactor]          # biomechanical + questionnaire, combined
    disclaimer: str = field(default=DISCLAIMER)


# Band cutpoints applied to percent-of-achievable-points (0..100).
# Illustrative tertile split, not derived from outcome data.
BAND_LOW_MAX = 34.0        # < 34%  -> "low"
BAND_MODERATE_MAX = 67.0   # 34-67% -> "moderate"; >= 67% -> "elevated"


def _band_for_percent(percent: float) -> Band:
    if percent < BAND_LOW_MAX:
        return "low"
    if percent < BAND_MODERATE_MAX:
        return "moderate"
    return "elevated"


# ============================================================
# SCORING FUNCTIONS
# ============================================================

def score_biomechanics(measurements: dict[str, float]) -> BiomechScore:
    """
    Apply BIOMECH_CRITERIA to whatever measurements the pipeline produced.

    Only criteria whose `measurement` key is present in `measurements` count
    toward max_points — a front-view clip is scored (and capped) only against
    frontal-plane criteria, a side-view clip only against sagittal-plane ones.
    This mirrors the pipeline's own view-aware design: we never invent a
    measurement the camera angle couldn't actually see.
    """
    points = 0.0
    max_points = 0.0
    factors: list[ContributingFactor] = []

    for criterion in BIOMECH_CRITERIA:
        if criterion.measurement not in measurements:
            continue
        max_points += criterion.points
        value = measurements[criterion.measurement]

        if criterion.direction == "abs_ge":
            triggered = abs(value) >= criterion.threshold
            comparison = f"|{value:g}| >= {criterion.threshold:g}"
        elif criterion.direction == "lt":
            triggered = value < criterion.threshold
            comparison = f"{value:g} < {criterion.threshold:g}"
        else:  # "ge"
            triggered = value >= criterion.threshold
            comparison = f"{value:g} >= {criterion.threshold:g}"

        if triggered:
            points += criterion.points
            factors.append(ContributingFactor(
                key=criterion.key,
                label=criterion.label,
                points=criterion.points,
                detail=(
                    f"{criterion.label}: measured {value:g} {criterion.unit} "
                    f"({comparison} {criterion.unit} screening threshold) — "
                    f"+{criterion.points:g} pts."
                ),
            ))

    return BiomechScore(points=points, max_points=max_points, factors=factors)


def score_questionnaire(answers: QuestionnaireAnswers | None) -> QuestionnaireScore | None:
    """
    Apply QUESTIONNAIRE_CRITERIA to self-reported answers.

    Returns None if `answers` itself is None (questionnaire skipped entirely).
    Individual unanswered fields within a partially-filled questionnaire are
    simply skipped (0 points, not counted toward max_points either), so a
    partial questionnaire never gets unfairly penalized for missing answers.
    """
    if answers is None:
        return None

    points = 0.0
    max_points = 0.0
    factors: list[ContributingFactor] = []

    if answers.previous_acl_injury is not None:
        max_points += PREVIOUS_ACL_INJURY_POINTS
        if answers.previous_acl_injury:
            points += PREVIOUS_ACL_INJURY_POINTS
            factors.append(ContributingFactor(
                key="previous_acl_injury",
                label="Previous ACL injury",
                points=PREVIOUS_ACL_INJURY_POINTS,
                detail=(
                    f"Reported a previous ACL injury — "
                    f"+{PREVIOUS_ACL_INJURY_POINTS:g} pts. {PREVIOUS_ACL_INJURY_CITATION}"
                ),
            ))

    if answers.sex is not None:
        max_points += FEMALE_SEX_POINTS
        if answers.sex == "female":
            points += FEMALE_SEX_POINTS
            factors.append(ContributingFactor(
                key="sex",
                label="Sex (epidemiological factor)",
                points=FEMALE_SEX_POINTS,
                detail=(
                    f"Reported sex: female — +{FEMALE_SEX_POINTS:g} pts. "
                    f"{FEMALE_SEX_CITATION}"
                ),
            ))

    if answers.sport_type is not None:
        sport_points = SPORT_TYPE_POINTS.get(answers.sport_type, 0.0)
        max_points += max(SPORT_TYPE_POINTS.values())
        if sport_points > 0:
            points += sport_points
            factors.append(ContributingFactor(
                key="sport_type",
                label="Sport type",
                points=sport_points,
                detail=(
                    f"Reported sport type: {answers.sport_type} — "
                    f"+{sport_points:g} pts. {SPORT_TYPE_CITATION}"
                ),
            ))

    if answers.age is not None:
        max_points += AGE_HIGH_INCIDENCE_POINTS
        if AGE_HIGH_INCIDENCE_MIN <= answers.age <= AGE_HIGH_INCIDENCE_MAX:
            points += AGE_HIGH_INCIDENCE_POINTS
            factors.append(ContributingFactor(
                key="age",
                label="Age (epidemiological factor)",
                points=AGE_HIGH_INCIDENCE_POINTS,
                detail=(
                    f"Reported age {answers.age} falls in the "
                    f"{AGE_HIGH_INCIDENCE_MIN}-{AGE_HIGH_INCIDENCE_MAX} higher-incidence "
                    f"range — +{AGE_HIGH_INCIDENCE_POINTS:g} pts. {AGE_CITATION}"
                ),
            ))

    if answers.activity_level is not None:
        max_points += COMPETITIVE_ACTIVITY_POINTS
        if answers.activity_level in ("competitive_high_school", "competitive_college_or_pro"):
            points += COMPETITIVE_ACTIVITY_POINTS
            factors.append(ContributingFactor(
                key="activity_level",
                label="Activity / competition level",
                points=COMPETITIVE_ACTIVITY_POINTS,
                detail=(
                    f"Reported activity level: {answers.activity_level} — "
                    f"+{COMPETITIVE_ACTIVITY_POINTS:g} pts. {COMPETITIVE_ACTIVITY_CITATION}"
                ),
            ))

    if answers.fatigue_reported is not None:
        max_points += FATIGUE_POINTS
        if answers.fatigue_reported:
            points += FATIGUE_POINTS
            factors.append(ContributingFactor(
                key="fatigue_reported",
                label="Reported fatigue",
                points=FATIGUE_POINTS,
                detail=f"Reported fatigue — +{FATIGUE_POINTS:g} pts. {FATIGUE_CITATION}",
            ))

    if answers.previous_lower_limb_injury is not None:
        max_points += PREVIOUS_LOWER_LIMB_INJURY_POINTS
        if answers.previous_lower_limb_injury:
            points += PREVIOUS_LOWER_LIMB_INJURY_POINTS
            factors.append(ContributingFactor(
                key="previous_lower_limb_injury",
                label="Previous lower-limb injury (non-ACL)",
                points=PREVIOUS_LOWER_LIMB_INJURY_POINTS,
                detail=(
                    f"Reported a previous lower-limb injury — "
                    f"+{PREVIOUS_LOWER_LIMB_INJURY_POINTS:g} pts. "
                    f"{PREVIOUS_LOWER_LIMB_INJURY_CITATION}"
                ),
            ))

    return QuestionnaireScore(points=points, max_points=max_points, factors=factors)


def compute_screening_score(
    measurements: dict[str, float],
    answers: QuestionnaireAnswers | None = None,
) -> ScreeningResult:
    """
    Combine biomechanical + (optional) questionnaire points into one
    screening result: a band, a percent-of-achievable score, and the full
    list of contributing factors in plain language.

    Returns NO injury probability, ever — see the module docstring.
    """
    biomech = score_biomechanics(measurements)
    questionnaire = score_questionnaire(answers)

    total_points = biomech.points + (questionnaire.points if questionnaire else 0.0)
    total_max_points = biomech.max_points + (questionnaire.max_points if questionnaire else 0.0)

    percent = (total_points / total_max_points * 100.0) if total_max_points > 0 else 0.0

    factors = list(biomech.factors)
    if questionnaire:
        factors.extend(questionnaire.factors)
    factors.sort(key=lambda f: f.points, reverse=True)

    return ScreeningResult(
        band=_band_for_percent(percent),
        percent_of_max=round(percent, 1),
        total_points=round(total_points, 2),
        total_max_points=round(total_max_points, 2),
        biomechanical=biomech,
        questionnaire=questionnaire,
        factors=factors,
    )
