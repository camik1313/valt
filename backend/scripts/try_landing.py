#!/usr/bin/env python3
# ============================================================
# try_landing.py — Part 3 experiment: find the landing frame in a
# real video and SAVE IT AS AN IMAGE so you can judge it yourself.
#
# The detector is a heuristic, so the real test is your eyes: does
# the frame it picked actually show the landing?
#
# HOW TO RUN (from backend/, with venv active):
#   python scripts/try_landing.py scripts/your_video.mp4
#
# OUTPUTS:
#   your_video_landing.jpg   <- the frame it thinks is the landing
#   your_video_peak.jpg      <- the highest point of the jump (context)
#   your_video_trajectory.txt <- hip height per frame, to inspect
# ============================================================

import sys
import cv2
import mediapipe as mp

# Import our detector from the app package.
from app.cv.landing_detector import detect_landing


def main(video_path: str) -> None:
    # ---- Pass 1: run MediaPipe over every frame, collecting landmarks ----
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ERROR: could not open video: {video_path}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    per_frame = []
    frames = []  # keep the raw images so we can save the chosen ones

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)
        if results.pose_landmarks:
            per_frame.append([
                (lm.x, lm.y, lm.z, lm.visibility)
                for lm in results.pose_landmarks.landmark
            ])
        else:
            per_frame.append(None)

    cap.release()
    pose.close()

    print(f"Read {len(frames)} frames at {fps:.0f} fps.")
    detected = sum(1 for f in per_frame if f is not None)
    print(f"Pose detected in {detected} frames.")

    # ---- Run the landing detector ----
    result = detect_landing(per_frame)

    print()
    print("=" * 58)
    print(f"  LANDING FRAME:     {result.landing_frame}"
          f"  (t = {result.landing_frame / fps:.2f}s)")
    print(f"  Jump peak frame:   {result.airborne_peak_frame}"
          f"  (t = {result.airborne_peak_frame / fps:.2f}s)")
    print(f"  Confident:         {result.confident}")
    print(f"  {result.note}")
    print("=" * 58)

    # ---- Save the chosen frames as images for visual inspection ----
    base = video_path.rsplit(".", 1)[0]

    if 0 <= result.landing_frame < len(frames):
        landing_path = f"{base}_landing.jpg"
        cv2.imwrite(landing_path, frames[result.landing_frame])
        print(f"\nSaved landing frame -> {landing_path}")

    if 0 <= result.airborne_peak_frame < len(frames):
        peak_path = f"{base}_peak.jpg"
        cv2.imwrite(peak_path, frames[result.airborne_peak_frame])
        print(f"Saved jump peak     -> {peak_path}")

    # ---- Save the trajectory so you can inspect the motion ----
    traj_path = f"{base}_trajectory.txt"
    with open(traj_path, "w") as f:
        f.write("frame\thip_y (smoothed; larger = lower in image)\n")
        for i, y in enumerate(result.trajectory):
            marker = ""
            if i == result.landing_frame:
                marker = "  <-- LANDING"
            elif i == result.airborne_peak_frame:
                marker = "  <-- JUMP PEAK"
            f.write(f"{i}\t{y:.4f}{marker}\n")
    print(f"Saved trajectory    -> {traj_path}")

    print("\nNOW LOOK AT THE LANDING IMAGE. Does it show the moment of")
    print("landing? That visual check is the real test of this step.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/try_landing.py path/to/video.mp4")
        sys.exit(1)
    main(sys.argv[1])
