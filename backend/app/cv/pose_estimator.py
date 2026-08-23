# ============================================================
# pose_estimator.py — the MediaPipe wrapper.
#
# ONE JOB: given a video file path, return the 33 pose landmarks for
# every frame. Nothing else. No angle math, no landing detection, no
# HTTP. That isolation is what makes this testable and swappable — if
# we ever replace MediaPipe with a different pose model, only this
# file changes.
#
# OUTPUT FORMAT: a list with one entry per frame. Each entry is either
#   - a list of 33 tuples (x, y, z, visibility), or
#   - None, if no body was detected in that frame.
# Coordinates are NORMALIZED: x and y run 0..1 across the image, where
# (0,0) is top-left. y grows DOWNWARD.
# ============================================================

from dataclasses import dataclass

import cv2
import mediapipe as mp

# One frame's landmarks, or None if no pose was found.
Landmarks = list[tuple[float, float, float, float]] | None

# A guided-capture clip runs ~11s (positioning + standing + jump + rebound).
# This caps arbitrary uploads (the /analyze fallback) generously above that,
# so a genuinely too-long video gets a clear rejection message instead of
# being silently truncated at MAX_FRAMES and analyzed as if it were complete.
MAX_VIDEO_SECONDS = 45


@dataclass
class PoseExtraction:
    """Everything we learned from reading the video."""
    per_frame: list[Landmarks]   # landmarks for each frame (None where missing)
    fps: float                   # frames per second
    width: int
    height: int
    frames_read: int
    frames_with_pose: int

    @property
    def detection_rate(self) -> float:
        """Fraction of frames where a body was found (0..1)."""
        if self.frames_read == 0:
            return 0.0
        return self.frames_with_pose / self.frames_read


def extract_landmarks(
    video_path: str,
    model_complexity: int = 1,
    max_frames: int | None = 900,
) -> PoseExtraction:
    """
    Run MediaPipe Pose over every frame of a video.

    Args:
        video_path: path to the video file.
        model_complexity: 0 = fastest/least accurate, 1 = balanced,
            2 = slowest/most accurate. We default to 1.
        max_frames: safety cap so an accidentally-long video can't tie up
            the server forever. ~900 frames is ~30 seconds at 30fps.

    Raises:
        ValueError: if the video can't be opened.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(
            "Couldn't open this video file. It may be corrupted or in an "
            "unsupported format — try re-exporting as .mp4 or .mov."
        )

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Fail fast on an oversized upload rather than silently analyzing only
    # its first MAX_VIDEO_SECONDS and treating that as the whole clip.
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    if frame_count and fps:
        duration_seconds = frame_count / fps
        if duration_seconds > MAX_VIDEO_SECONDS:
            cap.release()
            raise ValueError(
                f"This video is about {duration_seconds:.0f} seconds long. "
                f"Please trim it to the jump landing itself, under "
                f"{MAX_VIDEO_SECONDS} seconds."
            )

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,      # treat frames as a continuous sequence
        model_complexity=model_complexity,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    per_frame: list[Landmarks] = []
    frames_read = 0
    frames_with_pose = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break  # end of video

            frames_read += 1
            if max_frames is not None and frames_read > max_frames:
                break

            # MediaPipe wants RGB; OpenCV gives BGR. Convert.
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            if results.pose_landmarks:
                frames_with_pose += 1
                per_frame.append([
                    (lm.x, lm.y, lm.z, lm.visibility)
                    for lm in results.pose_landmarks.landmark
                ])
            else:
                per_frame.append(None)
    finally:
        # Always release resources, even if something above throws.
        cap.release()
        pose.close()

    return PoseExtraction(
        per_frame=per_frame,
        fps=fps,
        width=width,
        height=height,
        frames_read=len(per_frame),
        frames_with_pose=frames_with_pose,
    )
