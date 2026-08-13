# ============================================================
# less.py — the REAL Landing Error Scoring System (LESS). All 17 items,
# from the official scoring sheet and its primary validation paper —
# not an "inspired subset."
#
#   Padua DA, Marshall SW, Boling MC, Thigpen CA, Garrett WE Jr,
#   Beutler AI. The Landing Error Scoring System (LESS) Is a Valid and
#   Reliable Clinical Assessment Tool of Jump-Landing Biomechanics: The
#   JUMP-ACL Study. Am J Sports Med. 2009;37(10):1996-2002.
#   doi:10.1177/0363546509343200
#
# Risk cutoff (LESS score >= 5 -> classified high-risk; 86% sensitivity,
# 64% specificity; risk ratio 10.7 for injury within one season) from:
#   Padua DA, DiStefano LJ, Beutler AI, de la Motte SJ, DiStefano MJ,
#   Marshall SW. The Landing Error Scoring System as a Screening Tool
#   for an Anterior Cruciate Ligament Injury-Prevention Program in
#   Elite-Youth Soccer Athletes. J Athl Train. 2015;50(6):589-595.
#   doi:10.4085/1062-6050-50.1.10
#   IMPORTANT CAVEAT the paper itself notes: this cutoff was derived in
#   ELITE YOUTH SOCCER players. No population-specific cutoff has been
#   established for other sports, ages, or competition levels — treat
#   >=5 as an illustrative reference point outside that population, not
#   a validated universal threshold.
#
# HOW SCORING WORKS: the official protocol has an athlete perform 3
# jump-landing trials, scores each of the 17 items once PER TRIAL (see
# the "1 2 3" trial columns on the scoring sheet), then AVERAGES the 3
# trial totals. This app scores ONE trial per analysis (one uploaded
# clip), not three — an important limitation, stated plainly wherever
# the score is shown, not just here.
#
# WHAT THIS STILL ISN'T:
#   - NOT a diagnosis, not a trained/fitted model. This is a direct,
#     transparent implementation of a published clinical rating scale.
#   - NOT every item is computed from video. Two are fundamentally
#     transverse-plane (foot internal/external rotation at max flexion,
#     items 13-14) — invisible to any single 2D camera, front or side —
#     and one (item 17, "overall impression") is explicitly a holistic
#     clinical gestalt in the original tool, not a formula. These three
#     become a short LESS-worded questionnaire instead of a measurement
#     — see LessQuestionnaireAnswers below.
#   - Item 16 ("joint displacement, sagittal plane": soft/average/stiff)
#     IS auto-computed, but as a transparent PROXY — the total sagittal
#     displacement across knee+hip+trunk, banded into 3 tiers — not a
#     reproduction of the original rater's holistic visual judgment.
#   - Several items (2,3,5,6,7,8,9,10,11,12,15) describe a rater's
#     binary visual call ("hips are flexed", "trunk is vertical") with
#     no published numeric cutoff. Each is operationalized here with an
#     explicit, adjustable threshold, clearly marked OPERATIONALIZED in
#     its citation note so it's never mistaken for a number from the
#     original paper.
#   - Two full camera views (front AND side, e.g. this app's combined
#     capture session) are needed to score all 15 numeric items. A
#     single-view session only ever produces the 7 sagittal or 8
#     frontal items valid for that view — exactly like the rest of this
#     app's view-aware design (see cv/pipeline.py).
# ============================================================

from dataclasses import dataclass, field
from typing import Literal

Band = Literal["low", "moderate", "high"]

LESS_CITATION_PRIMARY = (
    "Padua DA, Marshall SW, Boling MC, Thigpen CA, Garrett WE Jr, Beutler AI. "
    "The Landing Error Scoring System (LESS) Is a Valid and Reliable Clinical "
    "Assessment Tool of Jump-Landing Biomechanics: The JUMP-ACL Study. "
    "Am J Sports Med. 2009;37(10):1996-2002. doi:10.1177/0363546509343200"
)
LESS_CITATION_CUTOFF = (
    "Padua DA, DiStefano LJ, Beutler AI, de la Motte SJ, DiStefano MJ, "
    "Marshall SW. The Landing Error Scoring System as a Screening Tool for "
    "an Anterior Cruciate Ligament Injury-Prevention Program in Elite-Youth "
    "Soccer Athletes. J Athl Train. 2015;50(6):589-595. "
    "doi:10.4085/1062-6050-50.1.10. Cutoff derived in elite youth soccer "
    "players; no population-specific cutoff exists for other groups."
)

DISCLAIMER = (
    "This is a real, direct implementation of the published 17-item Landing "
    "Error Scoring System (LESS), not a diagnosis and not a trained model. "
    "The official protocol averages 3 jump trials; this analysis scores one. "
    "Foot rotation (items 13-14) and overall impression (item 17) are "
    "self-reported, not measured, because they require either a transverse-"
    "plane view or a rater's holistic judgment that a 2D camera can't "
    "capture. A LESS score is a movement-quality screen, not a prediction "
    "of whether any individual will be injured, and should never replace "
    "assessment by a qualified clinician."
)

# Illustrative band edges around the literature's >=5 "high risk" cutoff.
BAND_LOW_MAX = 5      # score < 5 -> "low"
BAND_MODERATE_MAX = 9  # 5 <= score < 9 -> "moderate"; score >= 9 -> "high"


def band_for_score(score: float) -> Band:
    if score < BAND_LOW_MAX:
        return "low"
    if score < BAND_MODERATE_MAX:
        return "moderate"
    return "high"


# ============================================================
# ITEM DEFINITIONS
# ============================================================

@dataclass(frozen=True)
class LessItem:
    number: int
    key: str
    view: Literal["sagittal", "frontal", "overall"]
    label: str                 # the official sheet's short name
    good_criterion: str        # the official sheet's "no error" description
    max_points: int            # 1 for items 1-15, 2 for items 16-17
    operationalized: bool      # True if this item has no published numeric cutoff
    note: str                  # threshold + citation detail


SAGITTAL_ITEMS = [
    LessItem(1, "knee_flexion_ic", "sagittal",
             "Knee flexion angle at initial contact", "> 30 deg", 1, False,
             f"Threshold (30 deg) from the official LESS scoring sheet. {LESS_CITATION_PRIMARY}"),
    LessItem(2, "hip_flexion_ic", "sagittal",
             "Hip flexion angle at initial contact", "Hips are flexed", 1, True,
             "OPERATIONALIZED: the original item is a rater's binary visual call with no "
             "published angle. This app counts hip_flexion <= 10 deg as 'not flexed.'"),
    LessItem(3, "trunk_flexion_ic", "sagittal",
             "Trunk flexion angle at initial contact", "Trunk is flexed", 1, True,
             "OPERATIONALIZED: as with item 2, trunk forward lean <= 10 deg counts as 'not flexed.'"),
    LessItem(4, "knee_flexion_displacement", "sagittal",
             "Knee flexion displacement", "> 45 deg more than initial contact", 1, False,
             f"Threshold (45 deg) from the official LESS scoring sheet. {LESS_CITATION_PRIMARY}"),
    LessItem(5, "hip_flexion_displacement", "sagittal",
             "Hip flexion displacement", "Hips flex more than initial contact", 1, True,
             "OPERATIONALIZED: displacement <= 5 deg (essentially no further hip flexion "
             "after contact) counts as an error."),
    LessItem(6, "trunk_flexion_displacement", "sagittal",
             "Trunk flexion displacement", "Trunk flexes more than initial contact", 1, True,
             "OPERATIONALIZED: displacement <= 5 deg counts as an error."),
    LessItem(7, "ankle_plantarflexion_ic", "sagittal",
             "Ankle plantar-flexion angle at initial contact", "Toe to heel", 1, True,
             "OPERATIONALIZED from the foot-index/heel landmarks: toe not clearly lower "
             "than heel (offset <= 0.01 of frame height) counts as flat-footed/heel-first. "
             "LOWER CONFIDENCE than joint-angle items, since foot landmarks track less reliably."),
]

FRONTAL_ITEMS = [
    LessItem(8, "foot_contact_symmetry", "frontal",
             "Initial foot contact", "Symmetrical", 1, True,
             "OPERATIONALIZED: left/right ankles touching down more than 2 video frames "
             "apart (~65ms at 30fps) counts as asymmetric."),
    LessItem(9, "trunk_lateral_ic", "frontal",
             "Lateral trunk flexion at initial contact", "Trunk is vertical", 1, True,
             "OPERATIONALIZED: lateral lean >= 10 deg counts as 'not vertical.'"),
    LessItem(10, "knee_valgus_ic", "frontal",
             "Knee valgus angle at initial contact", "Knees over midfoot", 1, True,
             "OPERATIONALIZED: |medial displacement| >= 0.15 hip-widths on either knee "
             "counts as 'not over midfoot.'"),
    LessItem(11, "stance_width_narrow", "frontal",
             "Stance width, narrow", "< shoulder width", 1, False,
             f"'Error if YES' per the official LESS scoring sheet. {LESS_CITATION_PRIMARY}"),
    LessItem(12, "stance_width_wide", "frontal",
             "Stance width, wide", "> shoulder width", 1, False,
             f"'Error if YES' per the official LESS scoring sheet. {LESS_CITATION_PRIMARY}"),
    LessItem(15, "knee_valgus_displacement", "frontal",
             "Knee valgus displacement", "Medial knee movement at max flexion", 1, True,
             "OPERATIONALIZED: >= 0.10 hip-widths of ADDITIONAL medial movement (beyond "
             "the initial-contact position) on either knee counts as an error. The official "
             "sheet describes this qualitatively (tibial tubercle inside the first ray)."),
]

QUESTIONNAIRE_ITEMS = [
    LessItem(13, "foot_ir_max_flexion", "overall",
             "Max internal-rotation (IR) foot position", "Toes > 30 deg IR at max flexion", 1, True,
             "SELF-REPORTED, not measured: foot rotation is a transverse-plane motion no "
             "single 2D camera (front or side) can resolve reliably."),
    LessItem(14, "foot_er_max_flexion", "overall",
             "Max external-rotation (ER) foot position", "Toes > 30 deg ER at max flexion", 1, True,
             "SELF-REPORTED, not measured, for the same reason as item 13."),
    LessItem(17, "overall_impression", "overall",
             "Overall impression", "Excellent / Average / Poor", 2, True,
             "SELF-REPORTED, not measured: the official item is an explicit holistic "
             "clinical judgment across frontal, transverse, and stiffness patterns at once, "
             "not a formula. Scored 0 (excellent) / 1 (average) / 2 (poor), same as the "
             "official sheet."),
]

DISPLACEMENT_PROXY_ITEM = LessItem(
    16, "joint_displacement", "overall",
    "Joint displacement (sagittal plane)", "Soft / Average / Stiff", 2, True,
    "AUTO-COMPUTED PROXY, not the original rater's holistic judgment: banded from the "
    "total measured sagittal displacement (knee + hip + trunk flexion, initial contact to "
    "max flexion). >= 90 deg total = soft (0), 50-90 deg = average (1), < 50 deg = stiff (2).",
)

ALL_ITEMS = SAGITTAL_ITEMS + FRONTAL_ITEMS + [DISPLACEMENT_PROXY_ITEM] + QUESTIONNAIRE_ITEMS
MAX_LESS_SCORE = sum(i.max_points for i in ALL_ITEMS)  # 19

# Operationalized thresholds gathered in one place for easy adjustment.
HIP_TRUNK_FLEXED_MIN_DEG = 10.0
HIP_TRUNK_DISPLACEMENT_MIN_DEG = 5.0
TOE_TO_HEEL_MIN_OFFSET = 0.01
CONTACT_ASYMMETRY_MAX_FRAMES = 2
TRUNK_LATERAL_MAX_DEG = 10.0
KNEE_VALGUS_IC_MAX_HW = 0.15
KNEE_VALGUS_DISPLACEMENT_MAX_HW = 0.10
DISPLACEMENT_SOFT_MIN_DEG = 90.0
DISPLACEMENT_STIFF_MAX_DEG = 50.0


# ============================================================
# QUESTIONNAIRE (the 3 items no camera can score)
# ============================================================

@dataclass
class LessQuestionnaireAnswers:
    foot_ir_max_flexion: bool | None = None       # item 13: error if True
    foot_er_max_flexion: bool | None = None       # item 14: error if True
    overall_impression: Literal["excellent", "average", "poor"] | None = None  # item 17


# ============================================================
# RESULT SHAPES
# ============================================================

@dataclass
class LessItemScore:
    number: int
    key: str
    view: str
    label: str
    good_criterion: str
    points: int          # points actually awarded for this item (0, 1, or 2)
    max_points: int
    source: Literal["measured", "self_reported", "unavailable"]
    detail: str           # plain-language explanation of the score


@dataclass
class LessResult:
    total_points: float
    max_points: float          # only counts items this session could score
    percent_of_max: float
    band: Band
    items: list[LessItemScore]
    views_available: list[str]  # which of "front"/"side" contributed measurements
    disclaimer: str = field(default=DISCLAIMER)
    cutoff_citation: str = field(default=LESS_CITATION_CUTOFF)


# ============================================================
# SCORING
# ============================================================

def _worse_of(*values: float | None) -> float | None:
    present = [v for v in values if v is not None]
    if not present:
        return None
    return max(present, key=abs)


def _score_sagittal(raw: dict[str, float]) -> list[LessItemScore]:
    scores: list[LessItemScore] = []

    knee_flexion_ic = _worse_of(raw.get("less_knee_flexion_ic_left"), raw.get("less_knee_flexion_ic_right"))
    if knee_flexion_ic is not None:
        # "worse" for insufficient flexion means the SMALLER angle, so pick min not max.
        left, right = raw.get("less_knee_flexion_ic_left"), raw.get("less_knee_flexion_ic_right")
        val = min(v for v in (left, right) if v is not None)
        error = val <= 30.0
        scores.append(LessItemScore(
            1, "knee_flexion_ic", "sagittal", "Knee flexion at initial contact",
            "> 30 deg", 1 if error else 0, 1, "measured",
            f"Measured {val:g} deg at initial contact ({'<=' if error else '>'} 30 deg threshold).",
        ))

    hl, hr = raw.get("less_hip_flexion_ic_left"), raw.get("less_hip_flexion_ic_right")
    if hl is not None or hr is not None:
        val = min(v for v in (hl, hr) if v is not None)
        error = val <= HIP_TRUNK_FLEXED_MIN_DEG
        scores.append(LessItemScore(
            2, "hip_flexion_ic", "sagittal", "Hip flexion at initial contact", "Hips are flexed",
            1 if error else 0, 1, "measured",
            f"Measured {val:g} deg of hip flexion at initial contact "
            f"({'at or below' if error else 'above'} the {HIP_TRUNK_FLEXED_MIN_DEG:g} deg operationalized threshold).",
        ))

    if "less_trunk_flexion_ic" in raw:
        val = raw["less_trunk_flexion_ic"]
        error = val <= HIP_TRUNK_FLEXED_MIN_DEG
        scores.append(LessItemScore(
            3, "trunk_flexion_ic", "sagittal", "Trunk flexion at initial contact", "Trunk is flexed",
            1 if error else 0, 1, "measured",
            f"Measured {val:g} deg of forward trunk lean at initial contact.",
        ))

    kdl, kdr = raw.get("less_knee_flexion_displacement_left"), raw.get("less_knee_flexion_displacement_right")
    if kdl is not None or kdr is not None:
        val = min(v for v in (kdl, kdr) if v is not None)
        error = val <= 45.0
        scores.append(LessItemScore(
            4, "knee_flexion_displacement", "sagittal", "Knee flexion displacement",
            "> 45 deg more than initial contact", 1 if error else 0, 1, "measured",
            f"Knee flexed {val:g} deg more between initial contact and max flexion.",
        ))

    hdl, hdr = raw.get("less_hip_flexion_displacement_left"), raw.get("less_hip_flexion_displacement_right")
    if hdl is not None or hdr is not None:
        val = min(v for v in (hdl, hdr) if v is not None)
        error = val <= HIP_TRUNK_DISPLACEMENT_MIN_DEG
        scores.append(LessItemScore(
            5, "hip_flexion_displacement", "sagittal", "Hip flexion displacement",
            "Hips flex more than initial contact", 1 if error else 0, 1, "measured",
            f"Hip flexed {val:g} deg more between initial contact and max flexion.",
        ))

    if "less_trunk_flexion_displacement" in raw:
        val = raw["less_trunk_flexion_displacement"]
        error = val <= HIP_TRUNK_DISPLACEMENT_MIN_DEG
        scores.append(LessItemScore(
            6, "trunk_flexion_displacement", "sagittal", "Trunk flexion displacement",
            "Trunk flexes more than initial contact", 1 if error else 0, 1, "measured",
            f"Trunk flexed {val:g} deg more between initial contact and max flexion.",
        ))

    toe = _worse_of(raw.get("less_toe_to_heel_offset_left"), raw.get("less_toe_to_heel_offset_right"))
    if toe is not None:
        left, right = raw.get("less_toe_to_heel_offset_left"), raw.get("less_toe_to_heel_offset_right")
        val = min(v for v in (left, right) if v is not None)
        error = val <= TOE_TO_HEEL_MIN_OFFSET
        scores.append(LessItemScore(
            7, "ankle_plantarflexion_ic", "sagittal", "Ankle plantar-flexion at initial contact",
            "Toe to heel", 1 if error else 0, 1, "measured",
            f"Toe-vs-heel vertical offset {val:.3f} (lower-confidence foot-landmark measurement).",
        ))

    return scores


def _score_frontal(raw: dict[str, float]) -> list[LessItemScore]:
    scores: list[LessItemScore] = []

    if "less_foot_contact_asymmetry_frames" in raw:
        val = raw["less_foot_contact_asymmetry_frames"]
        error = val > CONTACT_ASYMMETRY_MAX_FRAMES
        scores.append(LessItemScore(
            8, "foot_contact_symmetry", "frontal", "Initial foot contact", "Symmetrical",
            1 if error else 0, 1, "measured",
            f"Feet touched down {val:g} frames apart "
            f"({'more' if error else 'no more'} than the {CONTACT_ASYMMETRY_MAX_FRAMES:g}-frame tolerance).",
        ))

    if "less_trunk_lateral_ic" in raw:
        val = raw["less_trunk_lateral_ic"]
        error = val >= TRUNK_LATERAL_MAX_DEG
        scores.append(LessItemScore(
            9, "trunk_lateral_ic", "frontal", "Lateral trunk flexion at initial contact",
            "Trunk is vertical", 1 if error else 0, 1, "measured",
            f"Measured {val:g} deg of lateral trunk lean at initial contact.",
        ))

    vl, vr = raw.get("less_knee_valgus_ic_left"), raw.get("less_knee_valgus_ic_right")
    if vl is not None or vr is not None:
        val = max((abs(v) for v in (vl, vr) if v is not None), default=0.0)
        error = val >= KNEE_VALGUS_IC_MAX_HW
        scores.append(LessItemScore(
            10, "knee_valgus_ic", "frontal", "Knee valgus at initial contact", "Knees over midfoot",
            1 if error else 0, 1, "measured",
            f"Largest medial knee deviation at initial contact: {val:g} hip-widths.",
        ))

    if "less_stance_width_ratio_ic" in raw:
        ratio = raw["less_stance_width_ratio_ic"]
        narrow_error = ratio < 1.0
        wide_error = ratio > 1.0
        scores.append(LessItemScore(
            11, "stance_width_narrow", "frontal", "Stance width, narrow", "< shoulder width",
            1 if narrow_error else 0, 1, "measured",
            f"Stance width was {ratio:.2f}x shoulder width at initial contact.",
        ))
        scores.append(LessItemScore(
            12, "stance_width_wide", "frontal", "Stance width, wide", "> shoulder width",
            1 if wide_error else 0, 1, "measured",
            f"Stance width was {ratio:.2f}x shoulder width at initial contact.",
        ))

    dl, dr = raw.get("less_knee_valgus_displacement_left"), raw.get("less_knee_valgus_displacement_right")
    if dl is not None or dr is not None:
        # More medial movement = more NEGATIVE-going or more POSITIVE-going
        # depending on side sign conventions already resolved upstream in
        # knee_valgus_index; here we just care about magnitude of change.
        val = max((abs(v) for v in (dl, dr) if v is not None), default=0.0)
        error = val >= KNEE_VALGUS_DISPLACEMENT_MAX_HW
        scores.append(LessItemScore(
            15, "knee_valgus_displacement", "frontal", "Knee valgus displacement",
            "Medial knee movement at max flexion", 1 if error else 0, 1, "measured",
            f"Largest additional medial knee movement from initial contact to max flexion: {val:g} hip-widths.",
        ))

    return scores


def _score_displacement_proxy(raw: dict[str, float]) -> LessItemScore | None:
    parts = [
        raw.get("less_knee_flexion_displacement_left"), raw.get("less_knee_flexion_displacement_right"),
        raw.get("less_hip_flexion_displacement_left"), raw.get("less_hip_flexion_displacement_right"),
        raw.get("less_trunk_flexion_displacement"),
    ]
    available = [p for p in parts if p is not None]
    if not available:
        return None
    total = sum(available)
    if total >= DISPLACEMENT_SOFT_MIN_DEG:
        points, label = 0, "soft"
    elif total >= DISPLACEMENT_STIFF_MAX_DEG:
        points, label = 1, "average"
    else:
        points, label = 2, "stiff"
    return LessItemScore(
        16, "joint_displacement", "overall", "Joint displacement (sagittal plane)",
        "Soft / Average / Stiff", points, 2, "measured",
        f"Total sagittal displacement (knee+hip+trunk) was {total:g} deg -> proxy band '{label}'.",
    )


def _score_questionnaire(answers: LessQuestionnaireAnswers | None) -> list[LessItemScore]:
    if answers is None:
        return []
    scores: list[LessItemScore] = []

    if answers.foot_ir_max_flexion is not None:
        scores.append(LessItemScore(
            13, "foot_ir_max_flexion", "overall", "Max internal-rotation (IR) foot position",
            "Toes > 30 deg IR at max flexion", 1 if answers.foot_ir_max_flexion else 0, 1,
            "self_reported",
            "Self-reported: " + ("toes turned in > 30 deg" if answers.foot_ir_max_flexion else "no excess internal rotation observed") + " at max knee flexion.",
        ))
    if answers.foot_er_max_flexion is not None:
        scores.append(LessItemScore(
            14, "foot_er_max_flexion", "overall", "Max external-rotation (ER) foot position",
            "Toes > 30 deg ER at max flexion", 1 if answers.foot_er_max_flexion else 0, 1,
            "self_reported",
            "Self-reported: " + ("toes turned out > 30 deg" if answers.foot_er_max_flexion else "no excess external rotation observed") + " at max knee flexion.",
        ))
    if answers.overall_impression is not None:
        points_map = {"excellent": 0, "average": 1, "poor": 2}
        points = points_map[answers.overall_impression]
        scores.append(LessItemScore(
            17, "overall_impression", "overall", "Overall impression",
            "Excellent / Average / Poor", points, 2, "self_reported",
            f"Self-reported overall impression: {answers.overall_impression}.",
        ))
    return scores


def compute_less_score(
    less_raw: dict[str, float],
    questionnaire: LessQuestionnaireAnswers | None = None,
) -> LessResult:
    """
    Combine whatever LESS-relevant raw measurements the pipeline produced
    (from a front clip, a side clip, or both — see cv/pipeline.py's
    less_raw) with the 3-item self-report questionnaire into a full LESS
    score. Only items this session could actually evaluate count toward
    max_points, so a single-view session is scored (and capped) fairly
    against its own achievable maximum, not penalized for items it never
    had the camera angle to see.
    """
    items: list[LessItemScore] = []
    views_available: list[str] = []

    sagittal = _score_sagittal(less_raw)
    if sagittal:
        views_available.append("side")
        items.extend(sagittal)

    frontal = _score_frontal(less_raw)
    if frontal:
        views_available.append("front")
        items.extend(frontal)

    proxy = _score_displacement_proxy(less_raw)
    if proxy is not None:
        items.append(proxy)

    items.extend(_score_questionnaire(questionnaire))

    total_points = sum(i.points for i in items)
    max_points = sum(i.max_points for i in items)
    percent = (total_points / max_points * 100.0) if max_points > 0 else 0.0

    return LessResult(
        total_points=total_points,
        max_points=max_points,
        percent_of_max=round(percent, 1),
        band=band_for_score(total_points),
        items=items,
        views_available=views_available,
    )
