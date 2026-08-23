# ============================================================
# test_report_service.py — proves build_analysis wires the screening
# risk score together correctly: populated when the real pipeline runs,
# absent on a mock fallback, and questionnaire-optional either way.
#
# We monkeypatch app.cv.pipeline.run_pipeline so these tests don't need
# a real video file — same technique the pipeline itself is decoupled
# for (see cv/pipeline.py's PipelineResult).
# ============================================================

import os
from unittest.mock import patch

import pytest

from app.cv.pipeline import PipelineResult
from app.models.schemas import QuestionnaireAnswers
from app.services import report_service


def _fake_front_view_result() -> PipelineResult:
    return PipelineResult(
        landing_frame=30,
        measurements={
            "knee_valgus_left": 0.20,
            "knee_valgus_right": 0.05,
            "valgus_asymmetry": 10.0,
            "trunk_lean_lateral": 5.0,
        },
        view="front",
        notes=["fake pipeline result for testing"],
        confident=True,
    )


def test_risk_score_populated_when_real_pipeline_succeeds():
    with patch("app.services.report_service.pipeline.run_pipeline", return_value=_fake_front_view_result()):
        analysis = report_service.build_analysis(
            upload_id="test123",
            athlete_name="Test Athlete",
            video_filename="jump.mp4",
            video_path="/fake/path.mp4",
            view="front",
        )

    assert analysis.risk_score is not None
    assert analysis.risk_score.questionnaire is None
    # Only knee_valgus_left (0.20 >= 0.15) triggers -> 2.0 of the front-view
    # biomechanical max of 7.0 (2 + 2 + 1.5 + 1.5).
    assert analysis.risk_score.biomechanical.points == 2.0
    assert analysis.risk_score.biomechanical.max_points == 7.0
    assert analysis.risk_score.total_points == 2.0
    assert "not a diagnosis" in analysis.risk_score.disclaimer.lower()


def test_risk_score_none_on_mock_fallback():
    # No video_path -> report_service falls back to the mock pipeline,
    # which has no real biomechanics, so no risk score should be fabricated.
    analysis = report_service.build_analysis(
        upload_id="test123",
        athlete_name="Test Athlete",
        video_filename="jump.mp4",
        video_path=None,
    )
    assert analysis.risk_score is None


def test_risk_score_includes_questionnaire_when_provided():
    questionnaire = QuestionnaireAnswers(previous_acl_injury=True)
    with patch("app.services.report_service.pipeline.run_pipeline", return_value=_fake_front_view_result()):
        analysis = report_service.build_analysis(
            upload_id="test123",
            athlete_name="Test Athlete",
            video_filename="jump.mp4",
            video_path="/fake/path.mp4",
            view="front",
            questionnaire=questionnaire,
        )

    assert analysis.risk_score is not None
    assert analysis.risk_score.questionnaire is not None
    assert analysis.risk_score.questionnaire.points == 4.0
    assert analysis.risk_score.total_points == 2.0 + 4.0


# ---- Combined front+side session (same-session second clip) ----

def _fake_side_view_result() -> PipelineResult:
    return PipelineResult(
        landing_frame=25,
        measurements={
            "knee_flexion_left": 40.0,   # < 55 deg threshold -> triggers +2 pts
            "knee_flexion_right": 70.0,
            "flexion_asymmetry": 5.0,
            "trunk_lean_forward": 35.0,
        },
        view="side",
        notes=["fake side-view pipeline result for testing"],
        confident=True,
    )


def test_combined_clip_merges_measurements_and_widens_risk_score():
    def side_effect(seed, video_path, view, **_kwargs):
        return _fake_side_view_result() if view == "side" else _fake_front_view_result()

    with patch("app.services.report_service.pipeline.run_pipeline", side_effect=side_effect):
        analysis = report_service.build_analysis(
            upload_id="test123",
            athlete_name="Test Athlete",
            video_filename="front.mp4",
            video_path="/fake/front.mp4",
            view="front",
            side_video_path="/fake/side.mp4",
            side_video_filename="side.mp4",
        )

    assert analysis.view == "front+side"
    assert analysis.video_filename == "front.mp4 + side.mp4"

    metric_keys = {m.key for m in analysis.metrics}
    assert {"knee_valgus_left", "knee_flexion_left"} <= metric_keys

    # Biomechanical max should now cover BOTH planes: 7.0 (front) + 7.5 (side).
    assert analysis.risk_score is not None
    assert analysis.risk_score.biomechanical.max_points == 14.5
    # knee_valgus_left (+2, front) and knee_flexion_left (+2, side) both trigger.
    assert analysis.risk_score.biomechanical.points == 4.0


def test_side_clip_failure_keeps_primary_clip_real_result():
    def side_effect(seed, video_path, view, **_kwargs):
        if view == "side":
            raise ValueError("no body detected in side clip")
        return _fake_front_view_result()

    with patch("app.services.report_service.pipeline.run_pipeline", side_effect=side_effect):
        analysis = report_service.build_analysis(
            upload_id="test123",
            athlete_name="Test Athlete",
            video_filename="front.mp4",
            video_path="/fake/front.mp4",
            view="front",
            side_video_path="/fake/side.mp4",
            side_video_filename="side.mp4",
        )

    # A failed second clip degrades to front-only, NOT a full mock fallback —
    # the primary clip's real measurements are still used.
    assert analysis.view == "front"
    assert analysis.risk_score is not None
    assert analysis.risk_score.biomechanical.max_points == 7.0
    assert "couldn't be analyzed" in analysis.summary


def test_no_side_clip_behaves_as_a_single_clip_analysis():
    with patch("app.services.report_service.pipeline.run_pipeline", return_value=_fake_front_view_result()):
        analysis = report_service.build_analysis(
            upload_id="test123",
            athlete_name="Test Athlete",
            video_filename="front.mp4",
            video_path="/fake/front.mp4",
            view="front",
        )
    assert analysis.view == "front"
    assert analysis.video_filename == "front.mp4"


# ---- Primary-clip failure: must raise, never fabricate a result ----

def test_primary_clip_failure_raises_instead_of_falling_back_to_mock():
    """
    A REAL video that the pipeline can't analyze (corrupted, no body
    detected, wrong orientation, etc.) must surface that specific error,
    not silently substitute fabricated numbers. This is the behavior
    change from the old "any pipeline exception -> mock fallback" design.
    """
    with patch(
        "app.services.report_service.pipeline.run_pipeline",
        side_effect=ValueError("No body was detected in this video."),
    ):
        with pytest.raises(ValueError, match="No body was detected"):
            report_service.build_analysis(
                upload_id="test123",
                athlete_name="Test Athlete",
                video_filename="jump.mp4",
                video_path="/fake/path.mp4",
                view="front",
            )


def test_video_path_none_still_uses_mock_deliberately():
    """
    The video_path=None path is a deliberate dev/demo toggle (no file to
    analyze at all), not a failure fallback — it must keep working exactly
    as before, clearly labeled as a simulated result.
    """
    analysis = report_service.build_analysis(
        upload_id="test123",
        athlete_name="Test Athlete",
        video_filename="jump.mp4",
        video_path=None,
    )
    assert analysis.risk_score is None
    assert "SIMULATED RESULT" in analysis.summary


# ---- Video deletion: the raw file should never outlive the analysis ----

def test_video_deleted_after_successful_analysis(tmp_path):
    video_path = tmp_path / "front.mp4"
    video_path.write_bytes(b"fake video bytes")

    with patch("app.services.report_service.pipeline.run_pipeline", return_value=_fake_front_view_result()):
        report_service.build_analysis(
            upload_id="test123",
            athlete_name="Test Athlete",
            video_filename="front.mp4",
            video_path=str(video_path),
            view="front",
        )

    assert not os.path.exists(video_path)


def test_both_videos_deleted_after_combined_session(tmp_path):
    front_path = tmp_path / "front.mp4"
    side_path = tmp_path / "side.mp4"
    front_path.write_bytes(b"fake front bytes")
    side_path.write_bytes(b"fake side bytes")

    def side_effect(seed, video_path, view, **_kwargs):
        return _fake_side_view_result() if view == "side" else _fake_front_view_result()

    with patch("app.services.report_service.pipeline.run_pipeline", side_effect=side_effect):
        report_service.build_analysis(
            upload_id="test123",
            athlete_name="Test Athlete",
            video_filename="front.mp4",
            video_path=str(front_path),
            view="front",
            side_video_path=str(side_path),
            side_video_filename="side.mp4",
        )

    assert not os.path.exists(front_path)
    assert not os.path.exists(side_path)


def test_video_deleted_after_primary_failure(tmp_path):
    video_path = tmp_path / "front.mp4"
    video_path.write_bytes(b"corrupted bytes")

    with patch(
        "app.services.report_service.pipeline.run_pipeline",
        side_effect=ValueError("Couldn't open this video file."),
    ):
        with pytest.raises(ValueError):
            report_service.build_analysis(
                upload_id="test123",
                athlete_name="Test Athlete",
                video_filename="front.mp4",
                video_path=str(video_path),
                view="front",
            )

    assert not os.path.exists(video_path)
