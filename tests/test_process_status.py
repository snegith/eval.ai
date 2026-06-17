"""Tests for full-process response status classification."""

from api.main import _process_stage_status


def test_process_status_ok_when_pipeline_succeeds():
    result = {
        "landmarks": {"landmarks_path": "data/sessions/session_x/landmarks.json"},
        "metrics": {
            "status": "ok",
            "metrics": {
                "eye_contact": {"eye_contact_score": 80},
                "posture": {"posture_score": 75},
                "animation": {"expressiveness_score": 70},
            },
        },
        "summary": {"status": "feedback_completed", "last_error": ""},
    }
    assert _process_stage_status(result) == "ok"


def test_process_status_partial_when_some_metrics_fail():
    result = {
        "landmarks": {"landmarks_path": "data/sessions/session_x/landmarks.json"},
        "metrics": {
            "status": "error",
            "metrics": {
                "eye_contact": {"eye_contact_score": 80},
                "posture": {"error": "Insufficient hip visibility for reliable posture scoring"},
                "animation": {"expressiveness_score": 70},
            },
        },
        "summary": {
            "status": "metrics_failed",
            "last_error": "posture: Insufficient hip visibility for reliable posture scoring",
        },
    }
    assert _process_stage_status(result) == "partial"


def test_process_status_error_when_landmarks_fail():
    result = {
        "landmarks": {"error": "No video file found for session session_x"},
        "summary": {"status": "landmarks_failed", "last_error": "No video file found"},
    }
    assert _process_stage_status(result) == "error"


def test_process_status_error_when_no_usable_metrics():
    result = {
        "landmarks": {"landmarks_path": "data/sessions/session_x/landmarks.json"},
        "metrics": {
            "status": "error",
            "metrics": {
                "eye_contact": {"error": "No face landmarks"},
                "posture": {"error": "Insufficient hip visibility"},
                "animation": {"error": "No face landmarks"},
            },
        },
        "summary": {"status": "metrics_failed", "last_error": "All metrics failed"},
    }
    assert _process_stage_status(result) == "error"
