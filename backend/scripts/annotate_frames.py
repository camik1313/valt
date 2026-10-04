#!/usr/bin/env python3
# ============================================================
# annotate_frames.py — SEE what the pipeline measured, on the actual frames.
#
# Runs the app's real pipeline on a clip, then saves annotated JPGs of the
# key moments (standing baseline, jump peak, initial contact, landing) with
# the skeleton, per-joint angles, and the numbers the report would show,
# plus a timeline of the hip trajectory and a text summary with sanity
# checks. The point is to let a human compare the overlay against what is
# visibly happening in the video, since the tests only cover synthetic
# geometry, not real footage.
#
# The overlay angles are recomputed with app.cv.metrics on the same
# landmarks the pipeline used; the "REPORTED" numbers come straight from
# pipeline.run_pipeline, so any disagreement is itself a finding.
#
# RUN (from backend/, venv active):
#   python -m scripts.annotate_frames scripts/your_clip.mp4 --view front
#   python -m scripts.annotate_frames scripts/your_clip.mp4 --view side
#
# Output goes to scripts/annotated/<clip name>/ (gitignored: it contains
# images of a real person).
# ============================================================

import argparse
import os

import cv2
import numpy as np

from app.cv import metrics, pipeline, pose_estimator
from app.cv.landing_detector import detect_landing, find_standing_window
from app.cv.pipeline import (
    L_ANKLE, L_FOOT_INDEX, L_HEEL, L_HIP, L_KNEE, L_SHOULDER,
    MIN_VISIBILITY,
    R_ANKLE, R_FOOT_INDEX, R_HEEL, R_HIP, R_KNEE, R_SHOULDER,
)

LEFT_COLOR = (255, 170, 40)    # BGR: blue-ish  (subject's LEFT)
RIGHT_COLOR = (40, 200, 255)   # BGR: amber     (subject's RIGHT)
TRUNK_COLOR = (80, 220, 80)
WHITE = (255, 255, 255)
RED = (60, 60, 255)

BONES = [
    (L_SHOULDER, R_SHOULDER, WHITE), (L_HIP, R_HIP, WHITE),
    (L_SHOULDER, L_HIP, LEFT_COLOR), (L_HIP, L_KNEE, LEFT_COLOR),
    (L_KNEE, L_ANKLE, LEFT_COLOR), (L_ANKLE, L_HEEL, LEFT_COLOR),
    (L_HEEL, L_FOOT_INDEX, LEFT_COLOR), (L_ANKLE, L_FOOT_INDEX, LEFT_COLOR),
    (R_SHOULDER, R_HIP, RIGHT_COLOR), (R_HIP, R_KNEE, RIGHT_COLOR),
    (R_KNEE, R_ANKLE, RIGHT_COLOR), (R_ANKLE, R_HEEL, RIGHT_COLOR),
    (R_HEEL, R_FOOT_INDEX, RIGHT_COLOR), (R_ANKLE, R_FOOT_INDEX, RIGHT_COLOR),
]
JOINTS = [
    L_SHOULDER, R_SHOULDER, L_HIP, R_HIP, L_KNEE, R_KNEE,
    L_ANKLE, R_ANKLE, L_HEEL, R_HEEL, L_FOOT_INDEX, R_FOOT_INDEX,
]


def grab_frames(video_path: str, wanted: set[int]) -> dict[int, "cv2.Mat"]:
    """Read frames sequentially (same decode path the pose extractor uses,
    so rotation/orientation handling matches) and keep only the ones we need."""
    cap = cv2.VideoCapture(video_path)
    frames: dict[int, "cv2.Mat"] = {}
    i = 0
    while wanted - frames.keys():
        ok, frame = cap.read()
        if not ok:
            break
        if i in wanted:
            frames[i] = frame
        i += 1
    cap.release()
    return frames


def put_text(img, text, org, scale, color=WHITE, thickness=1):
    """Text with a dark outline so it stays readable on any background."""
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thickness + 3, cv2.LINE_AA)
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def annotate(frame, lm, view: str, title: str, banner_lines: list[str]):
    img = frame.copy()
    h, w = img.shape[:2]
    scale = max(0.5, h / 1500)
    th = max(1, round(h / 900))

    def px(i):
        return (int(lm[i][0] * w), int(lm[i][1] * h))

    def pt(i):
        return (lm[i][0], lm[i][1])

    def vis(i):
        return lm[i][3] >= MIN_VISIBILITY

    # Skeleton
    for a, b, color in BONES:
        cv2.line(img, px(a), px(b), color, th + 1, cv2.LINE_AA)
    for j in JOINTS:
        low = not vis(j)
        cv2.circle(img, px(j), th + 4, RED if low else WHITE, -1 if low else th + 1, cv2.LINE_AA)

    # Subject's LEFT/RIGHT tags, so mirrored-camera mistakes are obvious.
    for ankle, tag, color in ((L_ANKLE, "L", LEFT_COLOR), (R_ANKLE, "R", RIGHT_COLOR)):
        x, y = px(ankle)
        put_text(img, tag, (x + 10, y + 30), scale * 1.4, color, th + 1)

    sh_mid = ((pt(L_SHOULDER)[0] + pt(R_SHOULDER)[0]) / 2, (pt(L_SHOULDER)[1] + pt(R_SHOULDER)[1]) / 2)
    hip_mid = ((pt(L_HIP)[0] + pt(R_HIP)[0]) / 2, (pt(L_HIP)[1] + pt(R_HIP)[1]) / 2)
    sh_mid_px = (int(sh_mid[0] * w), int(sh_mid[1] * h))
    hip_mid_px = (int(hip_mid[0] * w), int(hip_mid[1] * h))

    # Trunk line + the vertical it is measured against.
    if vis(L_SHOULDER) and vis(R_SHOULDER) and vis(L_HIP) and vis(R_HIP):
        cv2.line(img, hip_mid_px, sh_mid_px, TRUNK_COLOR, th + 2, cv2.LINE_AA)
        up = (hip_mid_px[0], max(0, hip_mid_px[1] - int(abs(sh_mid_px[1] - hip_mid_px[1]) * 1.2)))
        cv2.line(img, hip_mid_px, up, TRUNK_COLOR, 1, cv2.LINE_AA)
        lean = metrics.trunk_lean(sh_mid, hip_mid)
        label = "lateral lean" if view == "front" else "forward lean (magnitude)"
        put_text(img, f"trunk {label}: {lean:.1f} deg", (sh_mid_px[0] + 12, sh_mid_px[1]), scale, TRUNK_COLOR, th)

    if view == "side":
        for side, (s, hp, k, a, color) in (
            ("L", (L_SHOULDER, L_HIP, L_KNEE, L_ANKLE, LEFT_COLOR)),
            ("R", (R_SHOULDER, R_HIP, R_KNEE, R_ANKLE, RIGHT_COLOR)),
        ):
            if vis(hp) and vis(k) and vis(a):
                flex = metrics.knee_flexion(pt(hp), pt(k), pt(a))
                x, y = px(k)
                put_text(img, f"{side} knee flexion {flex:.0f} deg", (x + 14, y), scale, color, th)
            if vis(s) and vis(hp) and vis(k):
                hip_flex = metrics.hip_flexion(pt(s), pt(hp), pt(k))
                x, y = px(hp)
                put_text(img, f"{side} hip {hip_flex:.0f} deg", (x + 14, y), scale, color, th)
    else:
        hw = metrics.hip_width(pt(L_HIP), pt(R_HIP))
        for side, (hp, k, a, color) in (
            ("left", (L_HIP, L_KNEE, L_ANKLE, LEFT_COLOR)),
            ("right", (R_HIP, R_KNEE, R_ANKLE, RIGHT_COLOR)),
        ):
            if not (vis(hp) and vis(k) and vis(a)):
                continue
            # Reference: where the knee would sit if the leg were straight.
            t = (pt(k)[1] - pt(hp)[1]) / (pt(a)[1] - pt(hp)[1]) if abs(pt(a)[1] - pt(hp)[1]) > 1e-9 else 0.0
            line_x = pt(hp)[0] + t * (pt(a)[0] - pt(hp)[0])
            ref = (int(line_x * w), px(k)[1])
            cv2.line(img, px(hp), px(a), WHITE, 1, cv2.LINE_AA)
            cv2.line(img, ref, px(k), color, th + 2, cv2.LINE_AA)
            idx = metrics.knee_valgus_index(pt(hp), pt(k), pt(a), hw, side)
            x, y = px(k)
            put_text(img, f"{side[0].upper()} valgus idx {idx:+.2f} HW (raw)", (x + 14, y), scale, color, th)
        if vis(L_KNEE) and vis(R_KNEE) and vis(L_ANKLE) and vis(R_ANKLE):
            kasr = metrics.knee_ankle_separation_ratio(pt(L_KNEE), pt(R_KNEE), pt(L_ANKLE), pt(R_ANKLE))
            put_text(img, f"KASR {kasr:.2f}", (int(w * 0.04), int(h * 0.97)), scale, WHITE, th)

    # Banner (title + reported numbers).
    lines = [title] + banner_lines
    line_h = int(34 * scale * 1.5)
    box_h = line_h * len(lines) + 12
    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (w, box_h), (0, 0, 0), -1)
    img = cv2.addWeighted(overlay, 0.55, img, 0.45, 0)
    for n, text in enumerate(lines):
        put_text(img, text, (12, 12 + line_h * (n + 1) - int(line_h * 0.3)), scale * (1.1 if n == 0 else 0.9),
                 WHITE if n else (120, 255, 255), th)
    return img


def timeline_image(trajectory, events: dict[str, int | None], fps: float):
    """Hip height over time (up = higher body) with the detected events marked."""
    W, H, pad = 1200, 340, 40
    img = np.full((H, W, 3), 255, dtype=np.uint8)
    n = len(trajectory)
    lo, hi = min(trajectory), max(trajectory)
    span = (hi - lo) or 1.0

    def x_of(i):
        return int(pad + (W - 2 * pad) * i / max(1, n - 1))

    def y_of(v):  # trajectory is image-y (down = larger), so larger lands lower on the plot
        return int(pad + (H - 2 * pad) * (v - lo) / span)

    pts = [(x_of(i), y_of(v)) for i, v in enumerate(trajectory)]
    for a, b in zip(pts, pts[1:]):
        cv2.line(img, a, b, (90, 90, 90), 2, cv2.LINE_AA)
    colors = {
        "standing": (80, 180, 80), "peak": (200, 120, 0),
        "initial contact": (0, 140, 255), "landing (max flexion)": (60, 60, 230),
    }
    for row, (label, frame) in enumerate(events.items()):
        if frame is None:
            continue
        x = x_of(frame)
        c = colors.get(label, (0, 0, 0))
        cv2.line(img, (x, pad - 10), (x, H - pad + 10), c, 2)
        put_text(img, f"{label} f{frame} ({frame / fps:.2f}s)", (min(x + 4, W - 330), pad + 14 + 18 * row), 0.5, c, 1)
    put_text(img, "hip height over time (up = higher); vertical lines = detected events", (pad, H - 8), 0.5, (0, 0, 0), 1)
    return img


def vis_row(lm, label: str) -> str:
    names = {L_HIP: "L hip", L_KNEE: "L knee", L_ANKLE: "L ankle", R_HIP: "R hip", R_KNEE: "R knee", R_ANKLE: "R ankle"}
    cells = [f"{n} {lm[i][3]:.2f}{'*' if lm[i][3] < MIN_VISIBILITY else ''}" for i, n in names.items()]
    return f"{label}: " + ", ".join(cells) + "   (* = below visibility bar, joint is ignored)"


def main():
    ap = argparse.ArgumentParser(description="Annotate the key frames of a clip with what the pipeline measured.")
    ap.add_argument("video")
    ap.add_argument("--view", choices=["front", "side"], required=True)
    ap.add_argument("--out", default=None, help="output folder (default scripts/annotated/<clip name>)")
    args = ap.parse_args()

    stem = os.path.splitext(os.path.basename(args.video))[0]
    out_dir = args.out or os.path.join(os.path.dirname(__file__), "annotated", f"{stem}_{args.view}")
    os.makedirs(out_dir, exist_ok=True)

    print("Running the app's pipeline...")
    result = pipeline.run_pipeline(seed="annotate", video_path=args.video, view=args.view)
    print("Extracting landmarks for drawing...")
    ex = pose_estimator.extract_landmarks(args.video)
    landing = detect_landing(ex.per_frame)
    window = find_standing_window(ex.per_frame, landing.airborne_peak_frame) if args.view == "front" else None

    events: dict[str, int | None] = {
        "standing": (window[0] + window[1]) // 2 if window else None,
        "peak": landing.airborne_peak_frame,
        "initial contact": result.initial_contact_frame,
        "landing (max flexion)": result.landing_frame,
    }
    frames = grab_frames(args.video, {f for f in events.values() if f is not None})

    reported = [f"{k}: {v}" for k, v in result.measurements.items()]
    ic_values = [f"{k}: {v}" for k, v in result.less_raw.items() if "_ic" in k or "contact" in k][:10]
    per_event_lines = {
        "standing": ["standing baseline frame (valgus REPORTED = landing minus this)"],
        "peak": ["highest point of the jump, used to find the landing"],
        "initial contact": ["feet first touch (LESS 'at initial contact' items). REPORTED:"] + ic_values,
        "landing (max flexion)": ["max-flexion frame (the main report cards). REPORTED:"] + reported,
    }

    written = []
    for n, (label, frame_idx) in enumerate(events.items()):
        if frame_idx is None:
            print(f"  skipped '{label}': not found in this clip")
            continue
        lm = ex.per_frame[frame_idx]
        frame = frames.get(frame_idx)
        if lm is None or frame is None:
            print(f"  skipped '{label}': no pose/frame at {frame_idx}")
            continue
        title = f"{label.upper()} | frame {frame_idx} | {frame_idx / ex.fps:.2f}s | {args.view} view"
        img = annotate(frame, lm, args.view, title, per_event_lines[label])
        path = os.path.join(out_dir, f"{n + 1:02d}_{label.split(' (')[0].replace(' ', '_')}.jpg")
        cv2.imwrite(path, img)
        written.append(path)

    smoothed = [float(v) for v in landing.trajectory]
    cv2.imwrite(os.path.join(out_dir, "00_timeline.jpg"), timeline_image(smoothed, events, ex.fps))

    # Text summary with sanity checks.
    lines = [
        f"clip: {args.video}   view: {args.view}",
        f"frames: {ex.frames_read}  pose found: {ex.frames_with_pose} ({ex.detection_rate:.0%})  fps: {ex.fps:.1f}",
        f"events: " + ", ".join(f"{k}=f{v}" for k, v in events.items()),
        f"landing detector confident: {landing.confident}   pipeline confident: {result.confident}",
        "", "MEASUREMENTS (max-flexion frame):", *[f"  {k}: {v}" for k, v in result.measurements.items()],
        "", "LESS RAW:", *[f"  {k}: {v}" for k, v in result.less_raw.items()],
        "", "PIPELINE NOTES:", *[f"  - {n}" for n in result.notes],
        "", "SANITY CHECKS:",
    ]
    lm_land = ex.per_frame[result.landing_frame]
    if lm_land is not None:
        lines.append("  " + vis_row(lm_land, "visibility at landing"))
        for side, (h_, k_, a_) in (("left", (L_HIP, L_KNEE, L_ANKLE)), ("right", (R_HIP, R_KNEE, R_ANKLE))):
            ok = lm_land[h_][1] < lm_land[k_][1] < lm_land[a_][1]
            lines.append(f"  {side} leg joints ordered hip above knee above ankle: {'yes' if ok else 'NO (pose looks wrong)'}")
        mean_vis = {s: sum(lm_land[i][3] for i in idx) / 3 for s, idx in
                    (("left", (L_HIP, L_KNEE, L_ANKLE)), ("right", (R_HIP, R_KNEE, R_ANKLE)))}
        lines.append(f"  mean visibility left {mean_vis['left']:.2f} vs right {mean_vis['right']:.2f}")
        if args.view == "side" and abs(mean_vis["left"] - mean_vis["right"]) > 0.2:
            lines.append("  WARNING: one leg is much less visible than the other (far leg likely hidden behind "
                         "the near leg). Trust the near-side leg only; ignore left/right asymmetry.")
    summary_path = os.path.join(out_dir, "summary.txt")
    with open(summary_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print("\n".join(lines))
    print(f"\nWrote {len(written)} annotated frames + timeline + summary to {out_dir}")


if __name__ == "__main__":
    main()
