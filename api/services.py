import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from analysis.session_pipeline import run_feedback_stage, run_metrics_stage
from resume.parser import build_resume_artifacts
from resume.fallback_questions import build_fallback_questions
from resume.fallback_review import build_fallback_resume_review
from llm.resume_review import ResumeReviewError, generate_resume_review
from llm.question_generator import QuestionGenerationError, generate_questions_from_resume
from storage.session_store import (
    create_session,
    get_session_path,
    load_json,
    resolve_resume_path,
    resolve_video_path,
    save_json,
    session_exists,
    update_artifacts,
    update_metadata,
)
from video.landmarks import extract_landmarks
from video.validate_landmarks import validate_landmarks


ARTIFACT_FILENAMES = {
    "resume_text": "resume_text.json",
    "resume_profile": "resume_profile.json",
    "resume_review": "resume_review.json",
    "generated_questions": "generated_questions.json",
    "transcript": "transcript.json",
    "audio_metrics": "audio_metrics.json",
    "landmarks": "landmarks.json",
    "eye_contact": "eye_contact_results.json",
    "posture": "posture_results.json",
    "animation": "animation_results.json",
    "derived": "derived_results.json",
    "feedback": "feedback.json",
}


def ensure_session(session_id: str) -> None:
    if not session_exists(session_id):
        raise FileNotFoundError(f"Session not found: {session_id}")


def build_session_summary(session_id: str) -> Dict[str, Any]:
    metadata = load_json(session_id, "metadata.json")
    feedback = _safe_load_artifact(session_id, "feedback")
    overall_score = None
    if isinstance(feedback, dict) and "overall_score" in feedback:
        overall_score = feedback["overall_score"]

    return {
        "session_id": session_id,
        "created_at": metadata.get("created_at"),
        "updated_at": metadata.get("updated_at"),
        "status": metadata.get("status", "unknown"),
        "duration_seconds": float(metadata.get("duration_seconds", 0.0) or 0.0),
        "overall_score": overall_score,
        "has_feedback": bool(isinstance(feedback, dict) and not feedback.get("error")),
        "artifacts": metadata.get("artifacts", {}),
        "last_error": metadata.get("last_error", ""),
    }


def build_session_bundle(session_id: str) -> Dict[str, Any]:
    ensure_session(session_id)
    bundle: Dict[str, Any] = {
        "session_id": session_id,
        "metadata": load_json(session_id, "metadata.json"),
    }
    for key in ARTIFACT_FILENAMES:
        bundle[key] = _safe_load_artifact(session_id, key)
    return bundle


def create_empty_session() -> Dict[str, Any]:
    session_id = create_session()
    return build_session_summary(session_id)


def save_uploaded_video(session_id: str, source_path: str, original_filename: str) -> Dict[str, Any]:
    ensure_session(session_id)
    session_path = Path(get_session_path(session_id))
    session_path.mkdir(parents=True, exist_ok=True)

    suffix = Path(original_filename).suffix.lower() or ".mp4"
    canonical_name = f"video{suffix}"
    destination = session_path / canonical_name
    for existing_video in session_path.glob("video.*"):
        existing_video.unlink(missing_ok=True)
    shutil.copyfile(source_path, destination)

    update_artifacts(session_id, video=True)
    update_metadata(
        session_id,
        {
            "status": "video_uploaded",
            "video_filename": canonical_name,
            "last_error": "",
        },
    )

    return {
        "video_filename": canonical_name,
        "video_path": str(destination),
    }


def save_uploaded_resume(session_id: str, source_path: str, original_filename: str) -> Dict[str, Any]:
    ensure_session(session_id)
    session_path = Path(get_session_path(session_id))
    session_path.mkdir(parents=True, exist_ok=True)

    suffix = Path(original_filename).suffix.lower() or ".pdf"
    canonical_name = f"resume{suffix}"
    destination = session_path / canonical_name
    for existing_resume in session_path.glob("resume.*"):
        existing_resume.unlink(missing_ok=True)
    shutil.copyfile(source_path, destination)

    update_artifacts(session_id, resume=True, resume_text=False, resume_profile=False)
    update_metadata(
        session_id,
        {
            "resume_filename": canonical_name,
            "last_error": "",
        },
    )

    return {
        "resume_filename": canonical_name,
        "resume_path": str(destination),
    }


def parse_resume_for_session(session_id: str) -> Dict[str, Any]:
    ensure_session(session_id)
    resume_path = resolve_resume_path(session_id)
    if not resume_path:
        error = f"No resume file found for session {session_id}"
        update_metadata(session_id, {"status": "resume_parse_failed", "last_error": error})
        return {"error": error}

    artifacts = build_resume_artifacts(resume_path)
    resume_text = str(artifacts["resume_text"].get("full_text", ""))
    try:
        resume_review = generate_resume_review(
            resume_text,
            artifacts["resume_profile"],
        )
    except Exception as exc:
        # Gemini review is helpful but should never block the session once parsing succeeded.
        resume_review = build_fallback_resume_review(
            artifacts["resume_profile"],
            resume_text,
        )
        resume_review["_metadata"]["fallback_reason"] = str(exc)
    save_json(session_id, "resume_text.json", artifacts["resume_text"])
    save_json(session_id, "resume_profile.json", artifacts["resume_profile"])
    save_json(session_id, "resume_review.json", resume_review)
    update_artifacts(session_id, resume=True, resume_text=True, resume_profile=True, resume_review=True)
    update_metadata(
        session_id,
        {
            "status": "resume_parsed",
            "last_error": "",
        },
    )
    artifacts["resume_review"] = resume_review
    return artifacts


def generate_questions_for_session(session_id: str) -> Dict[str, Any]:
    ensure_session(session_id)
    session_path = Path(get_session_path(session_id))
    profile_path = session_path / "resume_profile.json"
    if not profile_path.exists():
        error = f"No parsed resume profile found for session {session_id}"
        update_metadata(session_id, {"status": "question_generation_failed", "last_error": error})
        return {"error": error}

    profile = load_json(session_id, "resume_profile.json")
    try:
        generated = generate_questions_from_resume(profile)
    except Exception as exc:
        generated = build_fallback_questions(profile)
        generated["_metadata"]["fallback_reason"] = str(exc)

    save_json(session_id, "generated_questions.json", generated)
    update_artifacts(session_id, questions=True)
    update_metadata(session_id, {"status": "questions_ready", "last_error": ""})
    return generated


def run_landmarks_for_session(session_id: str) -> Dict[str, Any]:
    ensure_session(session_id)
    video_path = resolve_video_path(session_id)
    if not video_path:
        error = f"No video file found for session {session_id}"
        update_metadata(session_id, {"status": "landmarks_failed", "last_error": error})
        return {"error": error}

    session_path = Path(get_session_path(session_id))
    output_path = session_path / "landmarks.json"

    extract_landmarks(video_path, str(output_path))
    report = validate_landmarks(str(output_path))
    save_json(session_id, "landmark_validation.json", report)
    update_artifacts(session_id, landmarks=True)
    update_metadata(
        session_id,
        {
            "status": "landmarks_extracted",
            "last_error": "",
        },
    )

    return {
        "landmarks_path": str(output_path),
        "validation": report,
    }


def run_full_processing_for_session(
    session_id: str,
    *,
    run_audio: bool = True,
    model_name: str = "base",
    pause_threshold: float = 2.0,
    generate_feedback: bool = True,
    parse_resume: bool = True,
    generate_questions: bool = True,
) -> Dict[str, Any]:
    ensure_session(session_id)
    results: Dict[str, Any] = {"session_id": session_id}

    if parse_resume and resolve_resume_path(session_id):
        results["resume"] = parse_resume_for_session(session_id)
        if generate_questions:
            results["questions"] = generate_questions_for_session(session_id)

    if run_audio:
        from analysis.audio_pipeline import run_audio_for_session

        try:
            results["audio"] = run_audio_for_session(
                session_id,
                model_name=model_name,
                pause_threshold=pause_threshold,
            )
        except Exception as exc:
            results["audio"] = {
                "error": f"Audio stage skipped: {exc}",
            }

    results["landmarks"] = run_landmarks_for_session(session_id)
    results["metrics"] = run_metrics_stage(session_id)
    if generate_feedback:
        results["feedback"] = run_feedback_stage(session_id)

    results["summary"] = build_session_summary(session_id)
    results["bundle"] = build_session_bundle(session_id)
    return results


def run_feedback_only(session_id: str) -> Dict[str, Any]:
    ensure_session(session_id)
    return run_feedback_stage(session_id)


def run_metrics_only(session_id: str) -> Dict[str, Any]:
    ensure_session(session_id)
    return run_metrics_stage(session_id)


def run_audio_only(session_id: str, model_name: str = "base", pause_threshold: float = 2.0) -> Dict[str, Any]:
    ensure_session(session_id)
    from analysis.audio_pipeline import run_audio_for_session

    return run_audio_for_session(session_id, model_name=model_name, pause_threshold=pause_threshold)


def _safe_load_artifact(session_id: str, artifact_key: str) -> Optional[Dict[str, Any]]:
    filename = ARTIFACT_FILENAMES.get(artifact_key)
    if not filename:
        return None
    path = Path(get_session_path(session_id)) / filename
    if not path.exists():
        return None
    try:
        return load_json(session_id, filename)
    except Exception:
        return {"error": f"Failed to load {filename}"}
