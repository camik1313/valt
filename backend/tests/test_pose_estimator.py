# ============================================================
# test_pose_estimator.py — the duration safety cap. Everything else in
# this module is exercised indirectly through test_pipeline.py's
# monkeypatched extraction, but the too-long-video rejection happens
# INSIDE extract_landmarks itself (before any pose processing), so it
# needs its own real video file to trigger.
# ============================================================

import cv2

from app.cv import pose_estimator


def _write_fake_video(path: str, fps: float, frame_count: int) -> None:
    """A tiny real video file with a known, cheap-to-create duration —
    low fps and a modest frame count keep this fast without needing
    MediaPipe to actually find a body in any frame (the duration check
    runs before that)."""
    writer = cv2.VideoWriter(
        path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (32, 32)
    )
    import numpy as np
    blank_frame = np.zeros((32, 32, 3), dtype="uint8")
    for _ in range(frame_count):
        writer.write(blank_frame)
    writer.release()


def test_rejects_video_longer_than_the_cap(tmp_path):
    # 2 fps * 100 frames = 50s, over the 45s cap.
    video_path = str(tmp_path / "too_long.mp4")
    _write_fake_video(video_path, fps=2.0, frame_count=100)

    try:
        pose_estimator.extract_landmarks(video_path)
        assert False, "expected a ValueError for an oversized video"
    except ValueError as exc:
        assert "seconds" in str(exc)


def test_accepts_video_under_the_cap(tmp_path):
    # 2 fps * 20 frames = 10s, comfortably under the 45s cap. Should pass
    # the duration check and proceed to (fast, blank-frame) pose extraction
    # rather than raising on duration.
    video_path = str(tmp_path / "short.mp4")
    _write_fake_video(video_path, fps=2.0, frame_count=20)

    result = pose_estimator.extract_landmarks(video_path)
    assert result.frames_read == 20
