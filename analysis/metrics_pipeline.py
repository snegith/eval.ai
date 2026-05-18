from pathlib import Path
from typing import Dict, Any
import json

from config import CONFIG
from storage.session_store import get_session_path, save_json
from video.eye_contact import analyze_eye_contact
from video.posture import analyze_posture
from video.facial_animation import analyze_facial_animation
from video.validate_landmarks import validate_landmarks


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _derive_confidence_score(eye_contact_pct: float, posture_pct: float) -> float:
    # Same formula as llm/feedback_prompt.py (promoted to persisted metrics)
    raw_confidence = (
        eye_contact_pct * CONFIG["confidence_eye_weight"]
    ) + (
        posture_pct * CONFIG["confidence_posture_weight"]
    )
    return min(CONFIG["confidence_cap"], raw_confidence * CONFIG["confidence_damping"])


def _derive_nervousness_score(consistency: float, stability: float) -> float:
    nervousness = 100.0 - (
        (consistency * CONFIG["nervousness_consistency_weight"])
        + (stability * CONFIG["nervousness_stability_weight"])
    )
    return _clamp(nervousness, 0.0, 100.0)


def run_metrics_for_session(session_id: str) -> Dict[str, Any]:
    """
    Run all landmark-based behavioral metrics for a given session.

    This function expects:
      - <BASE_DIR>/<session_id>/landmarks.json
    and will write:
      - eye_contact_results.json
      - posture_results.json
      - animation_results.json

    Returns a dictionary with keys:
      - eye_contact
      - posture
      - animation
    Each value is the corresponding analysis result dictionary.
    """
    session_path = Path(get_session_path(session_id))
    landmarks_path = session_path / "landmarks.json"

    if not landmarks_path.exists():
        error_msg = f"landmarks.json not found for session {session_id}"
        error_payload = {"error": error_msg}
        # Persist error stubs so the UI can render a clear message
        save_json(session_id, "eye_contact_results.json", error_payload)
        save_json(session_id, "posture_results.json", error_payload)
        save_json(session_id, "animation_results.json", error_payload)
        return {
            "eye_contact": error_payload,
            "posture": error_payload,
            "animation": error_payload,
        }

    def _error_payload(message: str, **extra: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"error": message}
        if extra:
            payload["debug_info"] = extra
        return payload

    # Quick sanity check: ensure landmarks.json looks like FaceMesh/Pose output
    try:
        with open(landmarks_path, "r") as f:
            landmarks_data = json.load(f)
        frames = landmarks_data.get("frames", [])
        sample_face_len = None
        sample_pose_len = None
        for fr in frames[:50]:
            face = fr.get("face_landmarks", [])
            pose = fr.get("pose_landmarks", [])
            if sample_face_len is None and face:
                sample_face_len = len(face)
            if sample_pose_len is None and pose:
                sample_pose_len = len(pose)
            if sample_face_len is not None and sample_pose_len is not None:
                break

        # If face landmarks exist but are not FaceMesh-sized, fail early with a clearer message.
        if sample_face_len is not None and sample_face_len < 200:
            error_msg = (
                f"Invalid landmarks.json format: expected FaceMesh landmarks (~468+ points), "
                f"but found face_landmarks length={sample_face_len}. "
                "This usually means MediaPipe Solutions is not installed/working. "
                "Recreate a Python 3.11 venv and reinstall requirements (mediapipe==0.10.14). "
                "Then rerun Phase 2 Landmark Extraction."
            )
            error_payload = {"error": error_msg}
            save_json(session_id, "eye_contact_results.json", error_payload)
            save_json(session_id, "posture_results.json", error_payload)
            save_json(session_id, "animation_results.json", error_payload)
            derived_payload = {"error": "Derived metrics require valid eye contact, posture, and animation results."}
            save_json(session_id, "derived_results.json", derived_payload)
            return {
                "eye_contact": error_payload,
                "posture": error_payload,
                "animation": error_payload,
                "derived": derived_payload,
            }
    except Exception:
        # If sanity-check fails, continue to analyzers which have their own error handling.
        pass

    try:
        coverage_report = validate_landmarks(str(landmarks_path))
    except Exception as e:
        coverage_report = {"error": f"Failed to validate landmarks.json: {e}"}

    # Run analyzers
    if coverage_report.get("error"):
        eye_contact_result = _error_payload(coverage_report["error"])
        posture_result = _error_payload(coverage_report["error"])
        animation_result = _error_payload(coverage_report["error"])
    else:
        face_coverage = float(coverage_report.get("face_coverage", 0.0))
        pose_coverage = float(coverage_report.get("pose_coverage", 0.0))
        pose_visibility_coverage = float(coverage_report.get("pose_visibility_coverage", 0.0))

        if face_coverage <= 0.0:
            eye_contact_result = _error_payload(
                "No usable FaceMesh frames detected in landmarks.json",
                coverage_report=coverage_report,
            )
            animation_result = _error_payload(
                "No usable FaceMesh frames detected in landmarks.json",
                coverage_report=coverage_report,
            )
        else:
            eye_contact_result = analyze_eye_contact(str(landmarks_path))
            animation_result = analyze_facial_animation(str(landmarks_path))

        if pose_coverage <= 0.0 or pose_visibility_coverage <= 0.0:
            posture_result = _error_payload(
                "No usable pose frames detected in landmarks.json",
                coverage_report=coverage_report,
            )
        else:
            posture_result = analyze_posture(str(landmarks_path))

    # Persist results per session
    save_json(session_id, "eye_contact_results.json", eye_contact_result)
    save_json(session_id, "posture_results.json", posture_result)
    save_json(session_id, "animation_results.json", animation_result)

    # Derived metrics (explainable, mathematical; not emotion classification)
    if any("error" in (res or {}) for res in [eye_contact_result, posture_result, animation_result]):
        derived_result: Dict[str, Any] = {
            "error": "Derived metrics require valid eye contact, posture, and animation results.",
        }
    else:
        eye_contact_pct = float(eye_contact_result.get("eye_contact_percentage", 0.0))
        posture_pct = float(posture_result.get("posture_percentage", 0.0))
        consistency = float(animation_result.get("consistency_score", 0.0))
        stability = float(animation_result.get("stability_score", 0.0))

        confidence = _derive_confidence_score(eye_contact_pct, posture_pct)
        nervousness = _derive_nervousness_score(consistency, stability)

        derived_result = {
            "confidence_score": round(confidence, 2),   # 0-95
            "nervousness_score": round(nervousness, 2), # 0-100 (higher = more variability/jitter)
            "source_metrics": {
                "eye_contact_percentage": round(eye_contact_pct, 2),
                "posture_percentage": round(posture_pct, 2),
                "consistency_score": round(consistency, 2),
                "stability_score": round(stability, 2),
            },
            "weights": {
                "confidence": {"eye_contact": 0.6, "posture": 0.4, "damping": 0.9, "cap": 95.0},
                "nervousness": {"consistency": 0.6, "stability": 0.4},
            },
        }

    save_json(session_id, "derived_results.json", derived_result)

    return {
        "eye_contact": eye_contact_result,
        "posture": posture_result,
        "animation": animation_result,
        "derived": derived_result,
    }

