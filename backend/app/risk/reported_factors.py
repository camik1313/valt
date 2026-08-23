# ============================================================
# risk/reported_factors.py — SELF-REPORTED RISK FACTORS.
#
# WHAT THIS IS: a plain list of epidemiological risk factors the athlete
# self-reports (prior ACL injury, sex, sport type, age, activity level,
# fatigue, prior lower-limb injury), included only when the answer
# matches a category the cited literature associates with elevated ACL
# injury risk. Every factor carries its own citation.
#
# WHAT THIS IS NOT:
#   - NOT a score. There is no points total, no weighting, no band. An
#     earlier version of this module combined these factors with a set
#     of illustrative biomechanical thresholds into a single weighted
#     "screening score." That composite was removed: the weights used to
#     compare factors as different as "prior ACL injury" and "reported
#     fatigue" were chosen by hand, not derived from outcome data, and a
#     single number built from them would overstate a precision the
#     underlying evidence doesn't support.
#   - NOT biomechanical. Measured movement mechanics (knee valgus,
#     flexion, trunk lean, asymmetry) already appear elsewhere in the
#     report as banded Metric cards and the Landing Profile summary, so
#     they aren't repeated here.
#   - NOT a diagnosis or a predictor. This never estimates an injury
#     probability for this athlete. Each factor below reflects a
#     population-level epidemiological pattern, not an individual one.
# ============================================================

from dataclasses import dataclass
from typing import Literal

Sex = Literal["female", "male", "other", "prefer_not_to_say"]
SportType = Literal["pivoting_cutting", "field_court_other", "endurance_noncontact", "other"]
ActivityLevel = Literal["sedentary", "recreational", "competitive_high_school", "competitive_college_or_pro"]


@dataclass
class QuestionnaireAnswers:
    """Every field is optional; an unanswered field simply can't produce a factor."""
    previous_acl_injury: bool | None = None
    sex: Sex | None = None
    sport_type: SportType | None = None
    age: int | None = None
    activity_level: ActivityLevel | None = None
    fatigue_reported: bool | None = None
    previous_lower_limb_injury: bool | None = None


@dataclass
class ReportedFactor:
    key: str
    label: str
    detail: str
    citation: str


# --- Citations, carried over unchanged from the earlier scored version,
# minus the point weights that used to sit next to each one. ---

PREVIOUS_ACL_INJURY_CITATION = (
    "Prior ACL injury is the single strongest known risk factor for a "
    "subsequent ACL injury (ipsilateral graft or contralateral); roughly "
    "1 in 4 young athletes sustain a second ACL injury within 24 months "
    "of return to sport (Paterno et al. 2014; Wiggins et al. 2016 "
    "meta-analysis)."
)

FEMALE_SEX_CITATION = (
    "Female athletes in pivoting/cutting sports show consistently higher "
    "non-contact ACL injury incidence than male athletes in the same "
    "sports in epidemiological studies (Prodromos et al. 2007 "
    "meta-analysis; Renstrom et al. 2008 IOC consensus statement). This "
    "reflects a population-level epidemiological pattern, not an "
    "individual prediction."
)

SPORT_TYPE_CITATION = (
    "Pivoting/cutting sports (e.g. soccer, basketball, handball, "
    "football) carry substantially higher reported ACL injury rates than "
    "straight-line endurance sports (Agel et al. 2005; Walden et al. "
    "2011)."
)

AGE_HIGH_INCIDENCE_MIN = 14
AGE_HIGH_INCIDENCE_MAX = 25
AGE_CITATION = (
    "Reported ACL injury incidence rises sharply in adolescence and "
    "stays elevated through the mid-20s in athletic populations (Beynnon "
    "et al. 2014; Shea et al. pediatric/adolescent incidence data), "
    "before declining. This is a population pattern, not an individual "
    "one."
)

COMPETITIVE_ACTIVITY_CITATION = (
    "Higher competitive exposure (more games/practices at a competitive "
    "level) means more at-risk landing/cutting exposures over time "
    "(Gornitzky et al. 2016 incidence-by-exposure analysis)."
)

FATIGUE_CITATION = (
    "Neuromuscular control of landing mechanics deteriorates under "
    "fatigue in laboratory studies (Chappell et al. 2005; Borotikar et "
    "al. 2008)."
)

PREVIOUS_LOWER_LIMB_INJURY_CITATION = (
    "A prior lower-limb injury (e.g. ankle sprain) is a general marker "
    "of elevated future lower-limb injury risk in systematic reviews "
    "(Swart et al. 2014), independent of ACL-specific mechanisms."
)


def reported_risk_factors(answers: QuestionnaireAnswers | None) -> list[ReportedFactor]:
    """
    Build the plain, unscored list of self-reported risk factors that
    match a literature-associated category. Returns an empty list when
    `answers` is None or nothing reported matches one.
    """
    if answers is None:
        return []

    factors: list[ReportedFactor] = []

    if answers.previous_acl_injury:
        factors.append(ReportedFactor(
            key="previous_acl_injury",
            label="Previous ACL injury",
            detail="Reported a previous ACL injury.",
            citation=PREVIOUS_ACL_INJURY_CITATION,
        ))

    if answers.sex == "female":
        factors.append(ReportedFactor(
            key="sex",
            label="Sex (epidemiological factor)",
            detail="Reported sex: female.",
            citation=FEMALE_SEX_CITATION,
        ))

    if answers.sport_type in ("pivoting_cutting", "field_court_other"):
        factors.append(ReportedFactor(
            key="sport_type",
            label="Sport type",
            detail=f"Reported sport type: {answers.sport_type}.",
            citation=SPORT_TYPE_CITATION,
        ))

    if answers.age is not None and AGE_HIGH_INCIDENCE_MIN <= answers.age <= AGE_HIGH_INCIDENCE_MAX:
        factors.append(ReportedFactor(
            key="age",
            label="Age (epidemiological factor)",
            detail=(
                f"Reported age {answers.age} falls in the "
                f"{AGE_HIGH_INCIDENCE_MIN}-{AGE_HIGH_INCIDENCE_MAX} higher-incidence range."
            ),
            citation=AGE_CITATION,
        ))

    if answers.activity_level in ("competitive_high_school", "competitive_college_or_pro"):
        factors.append(ReportedFactor(
            key="activity_level",
            label="Activity / competition level",
            detail=f"Reported activity level: {answers.activity_level}.",
            citation=COMPETITIVE_ACTIVITY_CITATION,
        ))

    if answers.fatigue_reported:
        factors.append(ReportedFactor(
            key="fatigue_reported",
            label="Reported fatigue",
            detail="Reported fatigue.",
            citation=FATIGUE_CITATION,
        ))

    if answers.previous_lower_limb_injury:
        factors.append(ReportedFactor(
            key="previous_lower_limb_injury",
            label="Previous lower-limb injury (non-ACL)",
            detail="Reported a previous lower-limb injury.",
            citation=PREVIOUS_LOWER_LIMB_INJURY_CITATION,
        ))

    return factors
