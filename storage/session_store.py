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

def list_sessions():
    base_path = Path(BASE_DIR)
    if not base_path.exists():
        return []
    return sorted([entry.name for entry in base_path.iterdir() if entry.is_dir()])

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
