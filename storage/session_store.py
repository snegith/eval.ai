import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from config import CONFIG

BASE_DIR = CONFIG["sessions_base_dir"]
SCHEMA_VERSION = "1.0"
VIDEO_BASENAME_CANDIDATES = (
    "video.mp4",
    "video.mov",
    "video.webm",
    "video.avi",
    "video.mkv",
)
RESUME_BASENAME_CANDIDATES = (
    "resume.pdf",
    "resume.txt",
    "resume.md",
)

ARTIFACT_FILES = {
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

DEFAULT_ARTIFACTS = {
    "video": False,
    "resume": False,
    "resume_text": False,
    "resume_profile": False,
    "resume_review": False,
    "questions": False,
    "audio": False,
    "transcript": False,
    "landmarks": False,
    "eye_contact": False,
    "posture": False,
    "animation": False,
    "derived": False,
    "feedback": False,
}

def create_session():
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    session_path = os.path.join(BASE_DIR, session_id)
    os.makedirs(session_path, exist_ok=True)

    metadata = {
        "session_id": session_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "status": "initialized",
        "schema_version": SCHEMA_VERSION,
        "video_filename": "video.mp4",
        "resume_filename": "",
        "duration_seconds": 0.0,
        "artifacts": {
            "video": False,
            "resume": False,
            "resume_text": False,
            "resume_profile": False,
            "resume_review": False,
            "questions": False,
            "audio": False,
            "transcript": False,
            "landmarks": False,
            "eye_contact": False,
            "posture": False,
            "animation": False,
            "derived": False,
            "feedback": False,
        },
        "last_error": "",
    }

    save_json(session_id, "metadata.json", metadata)
    return session_id

def get_session_path(session_id):
    return os.path.join(BASE_DIR, session_id)

def session_exists(session_id):
    return os.path.isdir(get_session_path(session_id))

def list_sessions(*, include_empty: bool = False):
    base_path = Path(BASE_DIR)
    if not base_path.exists():
        return []
    entries = sorted([entry.name for entry in base_path.iterdir() if entry.is_dir()])
    if include_empty:
        return entries
    return [session_id for session_id in entries if session_has_content(session_id)]


def session_has_content(session_id: str) -> bool:
    if resolve_video_path(session_id) or resolve_resume_path(session_id):
        return True
    session_path = Path(get_session_path(session_id))
    content_markers = (
        "landmarks.json",
        "eye_contact_results.json",
        "feedback.json",
        "transcript.json",
        "resume_profile.json",
        "generated_questions.json",
    )
    return any((session_path / name).exists() for name in content_markers)


def get_video_duration_seconds(video_path: str) -> float:
    import cv2

    capture = cv2.VideoCapture(video_path)
    try:
        fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
        if fps <= 0:
            return 0.0
        return float(frame_count / fps)
    finally:
        capture.release()


def _load_json_if_exists(session_id: str, filename: str):
    path = Path(get_session_path(session_id)) / filename
    if not path.exists():
        return None
    try:
        return load_json(session_id, filename)
    except Exception:
        return None


def _artifact_is_valid(session_id: str, artifact_key: str) -> bool:
    if artifact_key == "video":
        return resolve_video_path(session_id) is not None
    if artifact_key == "resume":
        return resolve_resume_path(session_id) is not None
    if artifact_key == "questions":
        filename = ARTIFACT_FILES["generated_questions"]
    else:
        filename = ARTIFACT_FILES.get(artifact_key)
    if not filename:
        return False

    path = Path(get_session_path(session_id)) / filename
    if not path.exists():
        return False

    payload = _load_json_if_exists(session_id, filename)
    if payload is None:
        return False
    if isinstance(payload, dict) and payload.get("error"):
        return False
    return True


def _resolve_duration_seconds(session_id: str) -> float:
    metadata = _load_json_if_exists(session_id, "metadata.json") or {}
    duration = float(metadata.get("duration_seconds") or 0.0)
    if duration > 0:
        return duration

    for filename in ("audio_metrics.json", "transcript.json"):
        payload = _load_json_if_exists(session_id, filename)
        if isinstance(payload, dict):
            duration = float(payload.get("duration_sec") or 0.0)
            if duration > 0:
                return duration

    landmarks = _load_json_if_exists(session_id, "landmarks.json")
    if isinstance(landmarks, dict):
        fps = float(landmarks.get("fps") or 0.0)
        total_frames = float(landmarks.get("total_frames") or 0.0)
        if fps > 0 and total_frames > 0:
            return total_frames / fps

    video_path = resolve_video_path(session_id)
    if video_path:
        return get_video_duration_seconds(video_path)
    return 0.0


def _infer_session_status(artifacts: dict, feedback_payload: dict | None) -> str:
    if artifacts.get("feedback") and isinstance(feedback_payload, dict) and not feedback_payload.get("error"):
        return "feedback_completed"
    if artifacts.get("feedback") and isinstance(feedback_payload, dict) and feedback_payload.get("error"):
        return "feedback_failed"
    if artifacts.get("landmarks"):
        metric_flags = [
            artifacts.get("eye_contact"),
            artifacts.get("posture"),
            artifacts.get("animation"),
        ]
        if any(metric_flags):
            if all(metric_flags) and artifacts.get("derived"):
                return "metrics_completed"
            return "metrics_failed"
        return "landmarks_extracted"
    if artifacts.get("audio") or artifacts.get("transcript"):
        return "audio_processed"
    if artifacts.get("questions"):
        return "questions_ready"
    if artifacts.get("resume_profile"):
        return "resume_parsed"
    if artifacts.get("resume"):
        return "resume_ready"
    if artifacts.get("video"):
        return "video_uploaded"
    return "initialized"


def _status_rank(status: str) -> int:
    order = {
        "initialized": 0,
        "video_uploaded": 1,
        "resume_ready": 2,
        "resume_parsed": 3,
        "audio_processed": 4,
        "landmarks_extracted": 5,
        "metrics_failed": 6,
        "metrics_completed": 7,
        "feedback_failed": 8,
        "feedback_completed": 9,
        "questions_ready": 10,
    }
    return order.get(status, 0)


def reconcile_session_metadata(session_id: str, *, write: bool = True) -> dict:
    metadata = load_json(session_id, "metadata.json")
    artifacts = {**DEFAULT_ARTIFACTS, **metadata.get("artifacts", {})}
    for key in DEFAULT_ARTIFACTS:
        artifacts[key] = _artifact_is_valid(session_id, key)

    feedback_payload = _load_json_if_exists(session_id, "feedback.json")
    inferred_status = _infer_session_status(artifacts, feedback_payload)
    current_status = str(metadata.get("status") or "initialized")
    duration_seconds = _resolve_duration_seconds(session_id)

    if current_status in {"initialized", ""} or not metadata.get("artifacts"):
        next_status = inferred_status
    elif _status_rank(inferred_status) > _status_rank(current_status):
        next_status = inferred_status
    else:
        next_status = current_status

    updates = {
        "artifacts": artifacts,
        "status": next_status,
        "duration_seconds": duration_seconds,
    }
    if resolve_video_path(session_id):
        video_name = Path(resolve_video_path(session_id)).name
        updates["video_filename"] = video_name
    if resolve_resume_path(session_id):
        updates["resume_filename"] = Path(resolve_resume_path(session_id)).name

    changed = (
        artifacts != metadata.get("artifacts")
        or next_status != current_status
        or duration_seconds != float(metadata.get("duration_seconds") or 0.0)
        or updates.get("video_filename") != metadata.get("video_filename")
        or updates.get("resume_filename") != metadata.get("resume_filename")
    )
    if write and changed:
        update_metadata(session_id, updates)
        return load_json(session_id, "metadata.json")

    metadata.update(updates)
    metadata["updated_at"] = metadata.get("updated_at", datetime.utcnow().isoformat())
    return metadata

def resolve_video_path(session_id):
    session_path = Path(get_session_path(session_id))
    for candidate in VIDEO_BASENAME_CANDIDATES:
        path = session_path / candidate
        if path.exists():
            return str(path)
    matches = sorted(session_path.glob("video.*"))
    if matches:
        return str(matches[0])
    return None

def resolve_resume_path(session_id):
    session_path = Path(get_session_path(session_id))
    for candidate in RESUME_BASENAME_CANDIDATES:
        path = session_path / candidate
        if path.exists():
            return str(path)
    matches = sorted(session_path.glob("resume.*"))
    if matches:
        return str(matches[0])
    return None

def save_json(session_id, filename, data):
    path = os.path.join(get_session_path(session_id), filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_json(session_id, filename):
    path = os.path.join(get_session_path(session_id), filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def update_metadata(session_id, updates):
    metadata = {}
    path = os.path.join(get_session_path(session_id), "metadata.json")
    if os.path.exists(path):
        metadata = load_json(session_id, "metadata.json")
    metadata.setdefault("schema_version", SCHEMA_VERSION)
    metadata.setdefault("video_filename", "video.mp4")
    metadata.setdefault("resume_filename", "")
    metadata.setdefault("duration_seconds", 0.0)
    metadata.setdefault("artifacts", {})
    metadata.setdefault("last_error", "")
    metadata.update(updates)
    metadata["updated_at"] = datetime.utcnow().isoformat()
    save_json(session_id, "metadata.json", metadata)
    return metadata

def update_artifacts(session_id, **artifact_updates):
    metadata = {}
    path = os.path.join(get_session_path(session_id), "metadata.json")
    if os.path.exists(path):
        metadata = load_json(session_id, "metadata.json")
    artifacts = metadata.get("artifacts", {})
    artifacts.update(artifact_updates)
    metadata["artifacts"] = artifacts
    metadata["updated_at"] = datetime.utcnow().isoformat()
    save_json(session_id, "metadata.json", metadata)
    return metadata
