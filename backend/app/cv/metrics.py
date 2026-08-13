# ============================================================
# metrics.py — the BIOMECHANICS MATH (the scientific core).
#
# Pure geometry: every function takes 2D points (x, y) and returns
# an angle in degrees. NO MediaPipe here — that keeps this file
# testable with hand-picked numbers where we already know the answer.
#
# COORDINATE SYSTEM NOTE (important):
# In image/video coordinates, x increases to the RIGHT and y increases
# DOWNWARD (0,0 is top-left). So a point lower on the body has a LARGER
# y. We account for this wherever "up" matters (e.g. trunk lean).
#
# A point is a tuple (x, y). Vectors are also (x, y).
# ============================================================

import math

Point = tuple[float, float]


# ---- Vector helpers -----------------------------------------

def _vector(frm: Point, to: Point) -> Point:
    """The arrow FROM one point TO another: (to - frm), component-wise."""
    return (to[0] - frm[0], to[1] - frm[1])


def _dot(a: Point, b: Point) -> float:
    """Dot product of two vectors: a.x*b.x + a.y*b.y."""
    return a[0] * b[0] + a[1] * b[1]


def _magnitude(v: Point) -> float:
    """Length of a vector: sqrt(x^2 + y^2) (Pythagoras)."""
    return math.hypot(v[0], v[1])


def angle_between(v1: Point, v2: Point) -> float:
    """
    Angle (in degrees) between two vectors, using the dot product.

    THE FORMULA:  cos(theta) = (v1 . v2) / (|v1| * |v2|)
    So:           theta = arccos( (v1 . v2) / (|v1| |v2|) )

    WHY IT WORKS (short version): the dot product equals
    |v1| |v2| cos(theta). Rearranging isolates cos(theta). arccos
    then recovers the angle. Result is always between 0 and 180 deg.
    """
    m1 = _magnitude(v1)
    m2 = _magnitude(v2)
    if m1 == 0 or m2 == 0:
        # A zero-length vector has no direction; angle is undefined.
        # Return 0.0 rather than crashing (caller can check inputs).
        return 0.0

    cos_theta = _dot(v1, v2) / (m1 * m2)
    # Floating-point math can push this a hair outside [-1, 1], which
    # would make arccos throw. Clamp it back into the valid range.
    cos_theta = max(-1.0, min(1.0, cos_theta))
    return math.degrees(math.acos(cos_theta))


# ---- Joint angles -------------------------------------------

def angle_at_joint(a: Point, b: Point, c: Point) -> float:
    """
    The INTERIOR angle at vertex b, formed by points a and c.

    We build two vectors that both start at b (the joint):
        b -> a   and   b -> c
    then measure the angle between them.

    Example: for the knee, call angle_at_joint(hip, knee, ankle).
    A straight leg (hip, knee, ankle in a line) gives ~180 deg.
    A right-angle bend gives ~90 deg.
    """
    return angle_between(_vector(b, a), _vector(b, c))


def knee_flexion(hip: Point, knee: Point, ankle: Point) -> float:
    """
    Knee flexion in degrees, using the convention:
        0 deg   = leg fully straight
        larger  = more bent (deeper landing)

    The raw interior angle is ~180 for a straight leg, so we report
    flexion = 180 - interior. A soft, deep landing has HIGH flexion.
    """
    interior = angle_at_joint(hip, knee, ankle)
    return 180.0 - interior


def hip_flexion(shoulder: Point, hip: Point, knee: Point) -> float:
    """
    Hip flexion in degrees. Same idea as the knee, using the joint
    above and below the hip: shoulder -> hip -> knee.
        0 deg  = trunk and thigh in a straight line (standing tall)
        larger = more hip bend (hinging/sitting into the landing)
    """
    interior = angle_at_joint(shoulder, hip, knee)
    return 180.0 - interior


def trunk_lean(shoulder_mid: Point, hip_mid: Point) -> float:
    """
    Trunk lean = how far the torso tilts from vertical, in degrees.

    The trunk vector points from the hip midpoint UP to the shoulder
    midpoint. In image coords "up" is negative-y, so straight-up is
    the vector (0, -1). We measure the angle between the trunk and
    that vertical reference.
        0 deg  = perfectly upright
        larger = more lean (forward or sideways; this magnitude
                 doesn't distinguish direction — see limitations)
    """
    trunk = _vector(hip_mid, shoulder_mid)  # from hips up to shoulders
    vertical_up = (0.0, -1.0)
    return angle_between(trunk, vertical_up)


def asymmetry_percent(left_value: float, right_value: float) -> float:
    """
    Left/right asymmetry as a percentage difference.

    Formula: |L - R| / mean(|L|, |R|) * 100.
    Symmetric (swapping L and R gives the same answer). Returns 0 if both 0.
    """
    mean = (abs(left_value) + abs(right_value)) / 2.0
    if mean == 0:
        return 0.0
    return abs(left_value - right_value) / mean * 100.0


# ============================================================
# FRONTAL-PLANE VALGUS (horizontal, foreshortening-proof)
#
# WHY NO ANGLE FUNCTION:
# The hip-knee-ankle angle from the front (the "Frontal Plane Projection
# Angle") is NOT reliable from a single 2D camera. During a landing the
# shin tilts toward the camera and FORESHORTENS (~35% shorter in test
# footage). A foreshortened shin makes a tiny sideways knee offset read as
# a huge angle: in real data an ~8 cm offset reported as 56 deg.
#
# THE FIX: foreshortening compresses depth (lengths, angles) but does NOT
# move x-coordinates sideways. So horizontal data is trustworthy — and
# sideways knee motion IS what valgus physically is. We measure horizontal
# knee displacement, normalized by hip width. The pipeline additionally
# compares this against the athlete's own standing baseline (captured in
# the same clip) to cancel body proportions, stance, and camera perspective.
# ============================================================

def hip_width(left_hip: Point, right_hip: Point) -> float:
    """Horizontal distance between the hips — the scale reference."""
    return abs(left_hip[0] - right_hip[0])


def knee_valgus_index(
    hip: Point, knee: Point, ankle: Point, hip_width_value: float, side: str
) -> float:
    """
    Frontal-plane knee deviation as a fraction of hip width.

        positive = MEDIAL  (knee toward midline -> valgus / knock-kneed)
        negative = LATERAL (knee away from midline -> varus / bow-legged)
        ~0       = knee tracks over the hip-ankle line

    e.g. 0.25 means the knee sits a quarter of a hip-width inside the
    straight line from hip to ankle.

    ONLY MEANINGFUL FROM A FRONT VIEW. Uses horizontal positions only, so
    it is immune to the shin foreshortening that corrupts angle methods.

    Args:
        hip_width_value: horizontal hip-to-hip distance (scale). Must be > 0.
        side: "left" or "right" (SUBJECT's anatomical side). In a front view
            the subject's LEFT appears on the image RIGHT, so "toward midline"
            is a different image-direction per leg.

    NOTE: assumes an un-mirrored front view (selfie cameras mirror the image).
    """
    if hip_width_value <= 1e-9:
        return 0.0

    hip_x, hip_y = hip
    knee_x, knee_y = knee
    ankle_x, ankle_y = ankle

    # Where the knee WOULD sit if the leg were straight: the point on the
    # hip->ankle line at the knee's height.
    if abs(ankle_y - hip_y) < 1e-9:
        return 0.0
    t = (knee_y - hip_y) / (ankle_y - hip_y)
    line_x = hip_x + t * (ankle_x - hip_x)

    # Pure horizontal offset (positive = knee right of the line in the image).
    deviation = knee_x - line_x

    # Convert image left/right into medial/lateral for this leg.
    medial = -deviation if side.lower() == "left" else deviation

    return medial / hip_width_value


def knee_ankle_separation_ratio(
    left_knee: Point, right_knee: Point, left_ankle: Point, right_ankle: Point
) -> float:
    """
    Knee-to-Ankle Separation Ratio (KASR): knee spacing / ankle spacing,
    horizontally.

        < 1 = knees closer than ankles -> VALGUS
        ~ 1 = knees over ankles
        > 1 = knees wider than ankles -> varus

    A ratio, so body size cancels. Immune to squat depth (unlike an angle).
    Still perspective-sensitive; compare to the standing baseline to correct.
    """
    knee_sep = abs(left_knee[0] - right_knee[0])
    ankle_sep = abs(left_ankle[0] - right_ankle[0])
    if ankle_sep <= 1e-9:
        return 1.0
    return knee_sep / ankle_sep


def lateral_trunk_lean(shoulder_mid: Point, hip_mid: Point) -> float:
    """
    Sideways trunk lean, from a FRONT view. Same geometry as trunk_lean();
    named separately so calling code is explicit about the plane. The trunk
    is a long near-vertical segment, so foreshortening barely affects it —
    unlike the leg angles, this one survives a front view.
    """
    return trunk_lean(shoulder_mid, hip_mid)


# ============================================================
# LESS-SPECIFIC GEOMETRY (front view)
#
# The Landing Error Scoring System (LESS) scores stance width against
# SHOULDER width specifically (not hip width, which knee_valgus_index
# uses) — see the official LESS scoring sheet, items 11-12.
#   Padua DA, Marshall SW, Boling MC, Thigpen CA, Garrett WE Jr,
#   Beutler AI. The Landing Error Scoring System (LESS) Is a Valid and
#   Reliable Clinical Assessment Tool of Jump-Landing Biomechanics: The
#   JUMP-ACL Study. Am J Sports Med. 2009;37(10):1996-2002.
# ============================================================

def stance_width_ratio(
    left_ankle: Point, right_ankle: Point, left_shoulder: Point, right_shoulder: Point
) -> float:
    """
    Foot stance width relative to shoulder width, horizontally.

        < 1 = feet narrower than shoulders (LESS item 11: "stance width narrow")
        ~ 1 = feet about shoulder-width apart
        > 1 = feet wider than shoulders (LESS item 12: "stance width wide")

    A ratio, so body size and camera distance mostly cancel (same idea as
    knee_ankle_separation_ratio).
    """
    shoulder_sep = abs(left_shoulder[0] - right_shoulder[0])
    ankle_sep = abs(left_ankle[0] - right_ankle[0])
    if shoulder_sep <= 1e-9:
        return 1.0
    return ankle_sep / shoulder_sep


def toe_to_heel_offset(heel: Point, toe: Point) -> float:
    """
    Vertical offset between the toe (MediaPipe's foot-index landmark) and
    heel at a single frame, in normalized image units (y grows DOWNWARD,
    so a larger y is lower/closer to the ground).

        positive = toe lower than heel -> forefoot touches first, the
                   "toe to heel" pattern LESS item 7 counts as no error
        ~0 or negative = flat-footed or heel-first contact -> the error case

    LOWER CONFIDENCE than joint-based measurements: MediaPipe's foot
    landmarks (heel/foot-index) are smaller and tracked less reliably than
    the major joints, especially in fast, motion-blurred phone footage.
    """
    return toe[1] - heel[1]
