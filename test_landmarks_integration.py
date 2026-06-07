"""Integration test: verify landmarks.py produces usable MediaPipe output."""
import json
import os
import tempfile

import pytest

from tests.conftest import default_test_video_path, mediapipe_runtime_ready
from video.landmarks import extract_landmarks
from video.validate_landmarks import validate_landmarks

DEFAULT_VIDEO_PATH = default_test_video_path()


@pytest.mark.skipif(
    not mediapipe_runtime_ready(),
    reason="MediaPipe requires protobuf<5 in a Python 3.11 virtual environment",
)
@pytest.mark.skipif(
    not os.path.exists(DEFAULT_VIDEO_PATH),
    reason=f"Test video not found at {DEFAULT_VIDEO_PATH}",
)
def test_landmarks_extraction_produces_valid_output():
    out_path = os.path.join(tempfile.gettempdir(), "landmarks_test.json")

    try:
        extract_landmarks(DEFAULT_VIDEO_PATH, out_path)

        with open(out_path, encoding="utf-8") as handle:
            data = json.load(handle)

        assert data["total_frames"] > 0, "Expected at least one frame in landmarks output"
        assert data["fps"] > 0, "Expected positive FPS in landmarks output"

        report = validate_landmarks(out_path)

        assert report["face_frames"] > 0, "Expected FaceMesh detections in at least one frame"
        assert report["pose_frames"] > 0, "Expected pose detections in at least one frame"
        assert report["pose_frames_with_visibility"] > 0, "Expected pose visibility fields"
    finally:
        if os.path.exists(out_path):
            os.remove(out_path)
