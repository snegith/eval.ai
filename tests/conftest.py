"""Shared pytest helpers for optional integration tests."""

import os


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
