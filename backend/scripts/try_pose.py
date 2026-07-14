#!/usr/bin/env python3
# ============================================================
# try_pose.py — a STANDALONE experiment (not part of the app yet).
#
# What it does, given a video file:
#   1. Opens the video with OpenCV, frame by frame.
#   2. Runs MediaPipe Pose on each frame to find 33 body landmarks.
#   3. Draws the skeleton onto each frame and saves a new "_pose.mp4"
#      video so you can WATCH the tracking and confirm it's working.
#   4. Prints a summary + the coordinates of the key joints (hips,
#      knees, ankles, shoulders) on the middle frame.
#
# HOW TO RUN (from the backend/ folder, with your venv active):
#   python scripts/try_pose.py path/to/your/video.mp4
#
# This is Part 1 of Stage 7: prove we can get real landmarks out of
# real video, in isolation, before wiring anything into the app.
# ============================================================

import sys
import cv2               # OpenCV: reads video, gives us frames as images
import mediapipe as mp   # MediaPipe: the pre-trained pose model


# ---- MediaPipe landmark index reference (the ones we care about) ----
# MediaPipe returns 33 landmarks; these are the joints our biomechanics
# needs. NOTE: "left"/"right" are the SUBJECT's anatomical sides. Filmed
# front-on, the subject's right side appears on the LEFT of the video.
KEY_LANDMARKS = {
    11: "L shoulder", 12: "R shoulder",
    23: "L hip",      24: "R hip",
    25: "L knee",     26: "R knee",
    27: "L ankle",    28: "R ankle",
}


def main(video_path: str) -> None:
    # ---- Open the input video ----
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ERROR: could not open video: {video_path}")
        sys.exit(1)

    # Read basic properties so our output video matches the input.
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Opened video: {width}x{height}, {fps:.0f} fps, ~{total_frames} frames")

    # ---- Set up the output (skeleton-overlay) video ----
    out_path = video_path.rsplit(".", 1)[0] + "_pose.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # codec for .mp4
    writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    # ---- Set up MediaPipe Pose ----
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    # model_complexity 1 = balanced accuracy/speed. 2 = most accurate/slowest.
    pose = mp_pose.Pose(
        static_image_mode=False,       # False = treat frames as a video sequence
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    # We'll store landmarks per frame so we can inspect one later.
    per_frame_landmarks = []
    frames_with_pose = 0
    frame_index = 0

    # ---- Main loop: read each frame ----
    while True:
        ok, frame = cap.read()
        if not ok:
            break  # no more frames

        # MediaPipe expects RGB; OpenCV gives us BGR. Convert.
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            frames_with_pose += 1
            # Save the 33 landmarks (normalized 0..1 x, y, z, visibility).
            landmarks = [
                (lm.x, lm.y, lm.z, lm.visibility)
                for lm in results.pose_landmarks.landmark
            ]
            per_frame_landmarks.append(landmarks)

            # Draw the skeleton onto the frame for the output video.
            mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
            )
        else:
            per_frame_landmarks.append(None)  # no body detected this frame

        writer.write(frame)
        frame_index += 1

    # ---- Clean up ----
    cap.release()
    writer.release()
    pose.close()

    # ---- Report what we found ----
    print(f"\nProcessed {frame_index} frames.")
    print(f"Pose detected in {frames_with_pose} of them.")
    print(f"Skeleton-overlay video saved to:\n  {out_path}")

    # Print the key-joint coordinates on the MIDDLE frame (a frame likely
    # to have a clean pose). Coordinates are normalized 0..1.
    if frames_with_pose > 0:
        mid = _first_valid_near_middle(per_frame_landmarks)
        if mid is not None:
            idx, landmarks = mid
            print(f"\nKey landmarks on frame {idx} (x, y are 0..1 of the image):")
            for i, name in KEY_LANDMARKS.items():
                x, y, _z, vis = landmarks[i]
                print(f"  [{i:2d}] {name:11s}  x={x:.3f}  y={y:.3f}  visibility={vis:.2f}")
    else:
        print("\nNo pose was detected in any frame. Tips: make sure the whole")
        print("body is in frame, lighting is good, and clothing is fairly fitted.")


def _first_valid_near_middle(per_frame_landmarks):
    """Find a frame near the middle that actually has landmarks."""
    n = len(per_frame_landmarks)
    if n == 0:
        return None
    middle = n // 2
    # Search outward from the middle for the first non-None frame.
    for offset in range(0, n):
        for idx in (middle + offset, middle - offset):
            if 0 <= idx < n and per_frame_landmarks[idx] is not None:
                return idx, per_frame_landmarks[idx]
    return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/try_pose.py path/to/video.mp4")
        sys.exit(1)
    main(sys.argv[1])
