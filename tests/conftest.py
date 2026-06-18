"""Shared pytest helpers for optional integration tests."""

import os
import shutil
import tempfile
from pathlib import Path

import pytest


def mediapipe_runtime_ready() -> bool:
    """Return True when MediaPipe can run with the pinned protobuf constraint."""
    try:
        from google.protobuf import __version__ as protobuf_version

        major = int(protobuf_version.split(".", 1)[0])
        if major >= 5:
            return False
    except Exception:
        return False

    try:
        import mediapipe  # noqa: F401
    except Exception:
        return False

    return True


def default_test_video_path() -> str:
    return os.environ.get(
        "LANDMARKS_TEST_VIDEO",
        "data/sessions/session_763c54f7/video.mp4",
    )


@pytest.fixture
def isolated_data_dir(monkeypatch):
    """Run tests against a temp data directory so existing sessions are untouched."""
    temp_root = Path(tempfile.mkdtemp(prefix="eval_ai_test_"))
    sessions_dir = temp_root / "sessions"
    sessions_dir.mkdir(parents=True)

    import storage.session_store as store

    original = store.BASE_DIR
    monkeypatch.setattr(store, "BASE_DIR", str(sessions_dir))
    try:
        yield sessions_dir
    finally:
        monkeypatch.setattr(store, "BASE_DIR", original)
        shutil.rmtree(temp_root, ignore_errors=True)
