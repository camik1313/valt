#!/usr/bin/env python3
# ============================================================
# inspect_frontal.py — WHY is valgus reading what it reads?
#
# Prints the raw frontal-plane geometry at the landing frame so we can
# see what the numbers are actually made of, and saves an annotated
# image of that frame.
#
# RUN (from backend/, venv active):
#   python -m scripts.inspect_frontal scripts/your_video.mp4
# ============================================================

import sys

import cv2
import mediapipe as mp

from app.cv import metrics, pose_estimator
from app.cv.landing_detector import detect_landing

L_SH, R_SH = 11, 12
L_HIP, R_HIP = 23, 24
L_KNEE, R_KNEE = 25, 26
L_ANK, R_ANK = 27, 28

NAMES = {
    L_SH: "L shoulder", R_SH: "R shoulder", L_HIP: "L hip", R_HIP: "R hip",
    L_KNEE: "L knee", R_KNEE: "R knee", L_ANK: "L ankle", R_ANK: "R ankle",
}


def main(video_path: str) -> None:
    print("Extracting landmarks...")
    ex = pose_estimator.extract_landmarks(video_path)
    print(f"  {ex.frames_read} frames, pose in {ex.frames_with_pose} ({ex.detection_rate:.0%})")

    landing = detect_landing(ex.per_frame)
    print(f"\nLanding frame: {landing.landing_frame} (peak {landing.airborne_peak_frame}), "
          f"confident={landing.confident}")

    lm = ex.per_frame[landing.landing_frame]
    if lm is None:
        print("No pose at the landing frame.")
        return

    def pt(i):
        return (lm[i][0], lm[i][1])

    # ---- Raw coordinates ----
    print("\nRAW LANDMARKS AT LANDING (x,y are 0..1; y grows DOWNWARD)")
    print(f"{'joint':<12}{'x':>8}{'y':>8}{'vis':>7}")
    for i, name in NAMES.items():
        x, y, _z, v = lm[i]
        flag = "  LOW" if v < 0.5 else ""
        print(f"{name:<12}{x:8.3f}{y:8.3f}{v:7.2f}{flag}")

    # ---- Is the pose anatomically sane? ----
    print("\nSANITY: is each joint below the one above it?")
    for side, (h, k, a) in (("LEFT", (L_HIP, L_KNEE, L_ANK)), ("RIGHT", (R_HIP, R_KNEE, R_ANK))):
        hy, ky, ay = lm[h][1], lm[k][1], lm[a][1]
        ok = hy < ky < ay
        print(f"  {side:5s} hip_y={hy:.3f} < knee_y={ky:.3f} < ankle_y={ay:.3f}  "
              f"-> {'OK' if ok else 'SUSPECT — joints out of order!'}")

    # ---- Horizontal separations (the KASR story) ----
    hip_sep = abs(lm[L_HIP][0] - lm[R_HIP][0])
    knee_sep = abs(lm[L_KNEE][0] - lm[R_KNEE][0])
    ank_sep = abs(lm[L_ANK][0] - lm[R_ANK][0])

    print("\nHORIZONTAL SEPARATIONS (fraction of frame width)")
    print(f"  hips  : {hip_sep:.3f}")
    print(f"  knees : {knee_sep:.3f}")
    print(f"  ankles: {ank_sep:.3f}")

    if ank_sep > 1e-6:
        kasr = knee_sep / ank_sep
        print(f"\n  KNEE-to-ANKLE SEPARATION RATIO (KASR) = {kasr:.3f}")
        if kasr < 0.9:
            verdict = "knees INSIDE ankles -> VALGUS (knock-kneed)"
        elif kasr > 1.1:
            verdict = "knees OUTSIDE ankles -> varus (bow-legged)"
        else:
            verdict = "knees track over ankles -> aligned"
        print(f"  -> {verdict}")
    else:
        print("\n  Ankles are at the same x — cannot compute KASR.")

    # ---- What the current (angle) formula produces, and why ----
    print("\nCURRENT FPPA-STYLE ANGLE (the number in your report)")
    for side, (h, k, a), tag in (("LEFT", (L_HIP, L_KNEE, L_ANK), "left"),
                                 ("RIGHT", (R_HIP, R_KNEE, R_ANK), "right")):
        interior = metrics.angle_at_joint(pt(h), pt(k), pt(a))
        signed = metrics.knee_valgus_signed(pt(h), pt(k), pt(a), side=tag)
        print(f"  {side:5s} interior hip-knee-ankle = {interior:6.1f} deg  "
              f"-> reported {signed:+6.1f} deg")

    print("\n  NOTE: this angle grows with SQUAT DEPTH and STANCE WIDTH, not just")
    print("  knee collapse. Deep landing + wide feet = big angle with zero valgus.")
    print("  That is why KASR above is the more trustworthy read.")

    # ---- Save the annotated frame ----
    cap = cv2.VideoCapture(video_path)
    img = None
    for i in range(landing.landing_frame + 1):
        ok, f = cap.read()
        if not ok:
            break
        if i == landing.landing_frame:
            img = f
    cap.release()

    if img is not None:
        mp_pose = mp.solutions.pose
        mp_draw = mp.solutions.drawing_utils
        with mp_pose.Pose(static_image_mode=True, model_complexity=1) as p:
            res = p.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            if res.pose_landmarks:
                mp_draw.draw_landmarks(img, res.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        out = video_path.rsplit(".", 1)[0] + "_frontal_check.jpg"
        cv2.imwrite(out, img)
        print(f"\nSaved annotated landing frame -> {out}")
        print("LOOK AT IT: is this a front-on view? Is it the landing? Are the")
        print("dots on the real joints? Are the knees actually caving inward?")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.inspect_frontal path/to/video.mp4")
        sys.exit(1)
    main(sys.argv[1])
