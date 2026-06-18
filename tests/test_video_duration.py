"""Tests for video duration capture on API upload."""

import os
from pathlib import Path

from api.services import save_uploaded_video
from storage.session_store import create_session, load_json
from tests.conftest import default_test_video_path


def test_save_uploaded_video_sets_duration_seconds(isolated_data_dir):
    test_video = default_test_video_path()
    if not os.path.exists(test_video):
        return

    session_id = create_session()
    result = save_uploaded_video(session_id, test_video, "sample.mp4")
    metadata = load_json(session_id, "metadata.json")

    assert result["duration_seconds"] > 0
    assert metadata["duration_seconds"] > 0
    assert (Path(isolated_data_dir) / session_id / "video.mp4").exists()
