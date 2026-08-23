# ============================================================
# test_report_service.py — proves build_analysis wires everything
# together correctly: self-reported risk factors, LESS score, exercise
# recommendations, and video cleanup.
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


def test_reported_factors_empty_without_questionnaire():
    with patch("app.services.report_service.pipeline.run_pipeline", return_value=_fake_front_view_result()):
        analysis = report_service.build_analysis(
            upload_id="test123",
            athlete_name="Test Athlete",
            video_filename="jump.mp4",
            video_path="/fake/path.mp4",
            view="front",
        )

    assert analysis.reported_factors == []


def test_reported_factors_computed_on_mock_fallback_when_questionnaire_given():
    # Reported factors come entirely from self-report, not measurements,
    # so unlike the LESS/recommendations sections they're still computed
    # even when the real pipeline didn't run.
    questionnaire = QuestionnaireAnswers(previous_acl_injury=True)
    analysis = report_service.build_analysis(
        upload_id="test123",
        athlete_name="Test Athlete",
        video_filename="jump.mp4",
        video_path=None,
        questionnaire=questionnaire,
    )
    assert any(f.key == "previous_acl_injury" for f in analysis.reported_factors)


def test_reported_factors_include_matching_questionnaire_answers():
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

    keys = {f.key for f in analysis.reported_factors}
    assert keys == {"previous_acl_injury"}
    factor = analysis.reported_factors[0]
    assert "previous acl injury" in factor.detail.lower()
    assert factor.citation


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


def test_combined_clip_merges_measurements_from_both_views():
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
    assert analysis.reported_factors == []
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


# ---- Exercise recommendations ----

def test_recommendations_computed_from_flagged_measurement():
    # _fake_front_view_result's knee_valgus_left=0.20 lands in the "watch"
    # band (threshold 0.15/0.25), which should surface as a
    # frontal_knee_control priority and matching exercises.
    questionnaire = QuestionnaireAnswers(age=16, current_pain_or_injury=False)
    with patch("app.services.report_service.pipeline.run_pipeline", return_value=_fake_front_view_result()):
        analysis = report_service.build_analysis(
            upload_id="test123",
            athlete_name="Test Athlete",
            video_filename="jump.mp4",
            video_path="/fake/path.mp4",
            view="front",
            questionnaire=questionnaire,
        )

    assert analysis.recommendations is not None
    assert analysis.recommendations.gated_reason is None
    assert any(p.target == "frontal_knee_control" for p in analysis.recommendations.priorities)
    assert analysis.recommendations.exercises
    assert all(analysis.recommendations.exercises[i].score >= analysis.recommendations.exercises[i + 1].score
               for i in range(len(analysis.recommendations.exercises) - 1))


def test_recommendations_filtered_by_specific_sport():
    questionnaire = QuestionnaireAnswers(age=16, current_pain_or_injury=False, specific_sport="soccer")
    with patch("app.services.report_service.pipeline.run_pipeline", return_value=_fake_front_view_result()):
        analysis = report_service.build_analysis(
            upload_id="test123",
            athlete_name="Test Athlete",
            video_filename="jump.mp4",
            video_path="/fake/path.mp4",
            view="front",
            questionnaire=questionnaire,
        )

    # Every exercise in the database lists the full jump/cut sport set, so
    # a real, tracked sport like "soccer" shouldn't exclude anything.
    assert analysis.recommendations is not None
    assert analysis.recommendations.exercises


def test_recommendations_not_zeroed_out_when_sport_is_other():
    """No exercise in the database lists "other" as a sport. Passing that
    straight through as a hard filter would silently zero out every
    recommendation, so report_service.py must map it to "no filter"
    instead — see _specific_sport_to_ranking_sport."""
    questionnaire = QuestionnaireAnswers(age=16, current_pain_or_injury=False, specific_sport="other")
    with patch("app.services.report_service.pipeline.run_pipeline", return_value=_fake_front_view_result()):
        analysis = report_service.build_analysis(
            upload_id="test123",
            athlete_name="Test Athlete",
            video_filename="jump.mp4",
            video_path="/fake/path.mp4",
            view="front",
            questionnaire=questionnaire,
        )

    assert analysis.recommendations is not None
    assert analysis.recommendations.exercises


def test_recommendations_gated_when_current_pain_or_injury_reported():
    questionnaire = QuestionnaireAnswers(age=16, current_pain_or_injury=True)
    with patch("app.services.report_service.pipeline.run_pipeline", return_value=_fake_front_view_result()):
        analysis = report_service.build_analysis(
            upload_id="test123",
            athlete_name="Test Athlete",
            video_filename="jump.mp4",
            video_path="/fake/path.mp4",
            view="front",
            questionnaire=questionnaire,
        )

    assert analysis.recommendations is not None
    assert analysis.recommendations.gated_reason is not None
    assert "healthcare professional" in analysis.recommendations.gated_reason
    assert analysis.recommendations.priorities == []
    assert analysis.recommendations.exercises == []


def test_recommendations_none_without_a_questionnaire():
    with patch("app.services.report_service.pipeline.run_pipeline", return_value=_fake_front_view_result()):
        analysis = report_service.build_analysis(
            upload_id="test123",
            athlete_name="Test Athlete",
            video_filename="jump.mp4",
            video_path="/fake/path.mp4",
            view="front",
        )

    assert analysis.recommendations is None


# ---- Landing profile ----

def test_landing_profile_populated_with_four_categories_no_questionnaire_needed():
    # Unlike recommendations, landing_profile needs no questionnaire —
    # just real measurements.
    with patch("app.services.report_service.pipeline.run_pipeline", return_value=_fake_front_view_result()):
        analysis = report_service.build_analysis(
            upload_id="test123",
            athlete_name="Test Athlete",
            video_filename="jump.mp4",
            video_path="/fake/path.mp4",
            view="front",
        )

    assert analysis.landing_profile is not None
    assert len(analysis.landing_profile.categories) == 4
    knee_control = next(c for c in analysis.landing_profile.categories if c.category == "knee_control")
    assert knee_control.rating == "watch"  # knee_valgus_left=0.20 lands in the watch band


def test_landing_profile_none_on_mock_fallback():
    analysis = report_service.build_analysis(
        upload_id="test123",
        athlete_name="Test Athlete",
        video_filename="jump.mp4",
        video_path=None,
    )
    assert analysis.landing_profile is None
