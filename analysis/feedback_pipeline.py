from pathlib import Path
from typing import Dict, Any

from storage.session_store import get_session_path, load_json, save_json
from llm.feedback_engine import generate_feedback, FeedbackGenerationError


def _safe_save_feedback(session_id: str, payload: Dict[str, Any]) -> None:
    try:
        save_json(session_id, "feedback.json", payload)
    except Exception:
        pass


def _load_metrics_for_session(session_id: str) -> Dict[str, Any]:
    """
    Load per-session metric JSONs and build the metrics dict expected
    by llm.feedback_prompt.validate_metrics.
    """
    session_dir = Path(get_session_path(session_id))

    eye_path = session_dir / "eye_contact_results.json"
    posture_path = session_dir / "posture_results.json"
    animation_path = session_dir / "animation_results.json"
    derived_path = session_dir / "derived_results.json"

    if not (eye_path.exists() and posture_path.exists() and animation_path.exists()):
        missing = []
        if not eye_path.exists():
            missing.append("eye_contact_results.json")
        if not posture_path.exists():
            missing.append("posture_results.json")
        if not animation_path.exists():
            missing.append("animation_results.json")
        raise FeedbackGenerationError(
            f"Missing metric files for session {session_id}: {', '.join(missing)}"
        )

    eye = load_json(session_id, "eye_contact_results.json")
    posture = load_json(session_id, "posture_results.json")
    animation = load_json(session_id, "animation_results.json")
    derived = load_json(session_id, "derived_results.json") if derived_path.exists() else {}

    metric_errors = []
    for name, payload in (
        ("eye_contact_results.json", eye),
        ("posture_results.json", posture),
        ("animation_results.json", animation),
    ):
        if isinstance(payload, dict) and payload.get("error"):
            metric_errors.append(f"{name}: {payload['error']}")

    if metric_errors:
        raise FeedbackGenerationError(
            "Cannot generate feedback because metric analysis failed: "
            + "; ".join(metric_errors)
        )

    if isinstance(derived, dict) and derived.get("error"):
        raise FeedbackGenerationError(
            "Cannot generate feedback because derived metric analysis failed: "
            f"derived_results.json: {derived['error']}"
        )

    # Map stored metrics into the 0-100 fields expected by validate_metrics
    metrics: Dict[str, Any] = {
        "eye_contact": float(eye.get("eye_contact_percentage", 0.0)),
        "eye_contact_grade": eye.get("grade", "Unknown"),
        "posture": float(posture.get("posture_percentage", 0.0)),
        "posture_grade": posture.get("grade", "Unknown"),
        "expressiveness": float(animation.get("expressiveness_score", 0.0)),
        "consistency": float(animation.get("consistency_score", 0.0)),
        "stability": float(animation.get("stability_score", 0.0)),
        "animation_grade": animation.get("grade", "Unknown"),
        "peak_frequency": float(
            animation.get("expression_dynamics", {})
            .get("peak_frequency_per_sec", 0.0)
        ),
    }

    if isinstance(derived, dict):
        if "confidence_score" in derived:
            metrics["confidence_score"] = float(derived["confidence_score"])
        if "nervousness_score" in derived:
            metrics["nervousness_score"] = float(derived["nervousness_score"])

    return metrics


def _load_transcript_for_session(session_id: str) -> str:
    """
    Load transcript text for a session.

    If transcript.json is missing or malformed, fall back to a placeholder
    so that behavioral-only feedback can still be generated.
    """
    try:
        transcript = load_json(session_id, "transcript.json")
    except FileNotFoundError:
        return "[No transcript available - analysis based on behavioral metrics only]"
    except Exception:
        return "[Transcript could not be loaded - analysis based on behavioral metrics only]"

    if isinstance(transcript, dict):
        text = transcript.get("full_text") or ""
    elif isinstance(transcript, str):
        text = transcript
    else:
        text = ""

    if not text.strip():
        return "[No transcript available - analysis based on behavioral metrics only]"

    return text


def run_feedback_for_session(session_id: str) -> Dict[str, Any]:
    """
    Generate LLM feedback for a given session and persist feedback.json.

    This function expects:
      - eye_contact_results.json
      - posture_results.json
      - animation_results.json
    and optionally:
      - transcript.json

    It writes:
      - feedback.json

    Returns the feedback dictionary (or an error payload).
    """
    try:
        metrics = _load_metrics_for_session(session_id)
        transcript_text = _load_transcript_for_session(session_id)

        feedback = generate_feedback(
            transcript=transcript_text,
            metrics=metrics,
        )

        _safe_save_feedback(session_id, feedback)
        return feedback

    except FeedbackGenerationError as e:
        error_payload = {
            "error": str(e),
        }
        # Persist error so the UI can show a graceful message
        _safe_save_feedback(session_id, error_payload)
        return error_payload

    except Exception as e:
        # Catch-all to avoid crashing callers; still persist an error marker.
        error_payload = {
            "error": f"Unexpected error while generating feedback: {e}",
        }
        _safe_save_feedback(session_id, error_payload)
        return error_payload

