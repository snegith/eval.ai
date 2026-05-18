from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from analysis.feedback_pipeline import run_feedback_for_session
from analysis.metrics_pipeline import run_metrics_for_session
from storage.session_store import get_session_path, update_artifacts, update_metadata


def _stage_has_error(result: Dict[str, Any], keys) -> bool:
    for key in keys:
        payload = result.get(key) or {}
        if isinstance(payload, dict) and payload.get("error"):
            return True
    return False


def _collect_stage_errors(result: Dict[str, Any], keys) -> str:
    messages = []
    for key in keys:
        payload = result.get(key) or {}
        if isinstance(payload, dict) and payload.get("error"):
            messages.append(f"{key}: {payload['error']}")
    return "; ".join(messages)


def run_metrics_stage(session_id: str) -> Dict[str, Any]:
    session_path = Path(get_session_path(session_id))
    landmarks_path = session_path / "landmarks.json"

    if not landmarks_path.exists():
        error = f"landmarks.json not found for session {session_id}"
        update_metadata(
            session_id,
            {
                "status": "metrics_failed",
                "last_error": error,
                "updated_at": datetime.utcnow().isoformat(),
            },
        )
        return {"status": "error", "error": error}

    metrics_result = run_metrics_for_session(session_id)
    has_error = _stage_has_error(metrics_result, ("eye_contact", "posture", "animation", "derived"))
    error_message = _collect_stage_errors(metrics_result, ("eye_contact", "posture", "animation", "derived"))

    update_artifacts(session_id, landmarks=True)
    update_metadata(
        session_id,
        {
            "status": "metrics_failed" if has_error else "metrics_completed",
            "last_error": error_message if has_error else "",
        },
    )
    update_artifacts(
        session_id,
        eye_contact=not bool((metrics_result.get("eye_contact") or {}).get("error")),
        posture=not bool((metrics_result.get("posture") or {}).get("error")),
        animation=not bool((metrics_result.get("animation") or {}).get("error")),
        derived=not bool((metrics_result.get("derived") or {}).get("error")),
    )

    return {
        "status": "error" if has_error else "ok",
        "metrics": metrics_result,
    }


def run_feedback_stage(session_id: str) -> Dict[str, Any]:
    feedback_result = run_feedback_for_session(session_id)
    has_error = isinstance(feedback_result, dict) and bool(feedback_result.get("error"))

    update_metadata(
        session_id,
        {
            "status": "feedback_failed" if has_error else "feedback_completed",
            "last_error": feedback_result.get("error", "") if has_error else "",
        },
    )
    update_artifacts(session_id, feedback=not has_error)

    return {
        "status": "error" if has_error else "ok",
        "feedback": feedback_result,
    }


def run_full_session_pipeline(session_id: str) -> Dict[str, Any]:
    metrics_stage = run_metrics_stage(session_id)
    if metrics_stage["status"] == "error":
        return {
            "status": "error",
            "metrics_stage": metrics_stage,
        }

    feedback_stage = run_feedback_stage(session_id)
    return {
        "status": feedback_stage["status"],
        "metrics_stage": metrics_stage,
        "feedback_stage": feedback_stage,
    }
