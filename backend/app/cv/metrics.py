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


def knee_valgus(hip: Point, knee: Point, ankle: Point) -> float:
    """
    Dynamic knee valgus, approximated by the Frontal Plane Projection
    Angle (FPPA): how far the knee deviates from the straight line
    between hip and ankle, viewed head-on.

    We reuse the interior hip-knee-ankle angle. Perfect vertical
    alignment gives ~180 deg; any inward (or outward) knee deviation
    reduces it. We report the DEVIATION from straight:
        0 deg  = knee tracks straight over the ankle
        larger = more collapse (valgus if inward)

    LIMITATION: from a single 2D view this magnitude doesn't tell
    valgus (inward) from varus (outward) on its own, and it depends
    on the camera being roughly front-on. We document this in Part 5.
    """
    interior = angle_at_joint(hip, knee, ankle)
    return 180.0 - interior


def asymmetry_percent(left_value: float, right_value: float) -> float:
    """
    Left/right asymmetry as a percentage difference.

    Formula: |L - R| / mean(L, R) * 100.
    Using the mean as the denominator makes it symmetric (swapping
    L and R gives the same answer). Returns 0 if both are 0.
    """
    mean = (abs(left_value) + abs(right_value)) / 2.0
    if mean == 0:
        return 0.0
    return abs(left_value - right_value) / mean * 100.0


# ---- Signed valgus (frontal plane) ---------------------------

def knee_valgus_signed(hip: Point, knee: Point, ankle: Point, side: str) -> float:
    """
    Dynamic knee valgus in degrees, WITH DIRECTION.

        positive = VALGUS  (knee caves toward the body's midline — "knock-kneed")
        negative = VARUS   (knee bows away from the midline — "bow-legged")
        ~0       = knee tracks straight over the ankle

    ONLY MEANINGFUL FROM A FRONT-ON VIEW. Valgus is a frontal-plane motion;
    from a side view this number is measuring knee flexion instead and is
    scientifically meaningless. The caller must know its camera view.

    HOW IT WORKS:
      1. The MAGNITUDE is the 2D deviation of the hip-knee-ankle angle from
         straight (180 deg) — the standard Frontal Plane Projection Angle idea.
      2. The DIRECTION comes from comparing the knee's x-position against the
         straight line from hip to ankle. If the knee sits toward the midline,
         that's valgus; away from it, varus. The plain angle cannot tell these
         apart, which is why we compute the sign separately.

    Args:
        side: "left" or "right" — the SUBJECT'S anatomical side. Needed because
            in a front-on view the subject's LEFT appears on the image's RIGHT,
            so "toward the midline" is a different x-direction for each leg.

    NOTE: assumes an un-mirrored front view. Phone selfie cameras mirror the
    image, which would swap left and right.
    """
    magnitude = 180.0 - angle_at_joint(hip, knee, ankle)

    hip_x, hip_y = hip
    knee_x, knee_y = knee
    ankle_x, ankle_y = ankle

    # Where would the knee be if the leg were perfectly straight? Find the
    # point on the hip->ankle line at the knee's height.
    if abs(ankle_y - hip_y) < 1e-9:
        return 0.0  # degenerate: hip and ankle at the same height
    t = (knee_y - hip_y) / (ankle_y - hip_y)
    line_x = hip_x + t * (ankle_x - hip_x)

    # How far, horizontally, is the real knee from that straight-leg line?
    # Positive means the knee sits to the RIGHT of the line in the image.
    horizontal_deviation = knee_x - line_x

    # Convert "image right/left" into "medial/lateral" for this leg.
    # Front-on: subject's LEFT leg appears on the image RIGHT, so medial
    # (toward midline) means moving LEFT in the image = negative deviation.
    if side.lower() == "left":
        medial = -horizontal_deviation
    else:
        medial = horizontal_deviation

    return magnitude if medial >= 0 else -magnitude


def lateral_trunk_lean(shoulder_mid: Point, hip_mid: Point) -> float:
    """
    Sideways trunk lean, from a FRONT view. Same geometry as trunk_lean();
    named separately so the calling code is explicit about which plane it
    is measuring. From a front camera, trunk_lean() captures LATERAL tilt.
    """
    return trunk_lean(shoulder_mid, hip_mid)
