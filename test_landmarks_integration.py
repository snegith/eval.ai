"""Quick integration test: verify landmarks.py produces usable MediaPipe output."""
import json
import os
import tempfile

from video.landmarks import extract_landmarks
from video.validate_landmarks import validate_landmarks


video_path = "data/sessions/session_763c54f7/video.mp4"
out_path = os.path.join(tempfile.gettempdir(), "landmarks_test.json")

print("Extracting landmarks...")
extract_landmarks(video_path, out_path)

with open(out_path) as f:
    data = json.load(f)

assert data["total_frames"] > 0, "Expected at least one frame in landmarks output"
assert data["fps"] > 0, "Expected positive FPS in landmarks output"

report = validate_landmarks(out_path)
print("Validation report:", report)

assert report["face_frames"] > 0, "Expected FaceMesh detections in at least one frame"
assert report["pose_frames"] > 0, "Expected pose detections in at least one frame"
assert report["pose_frames_with_visibility"] > 0, "Expected pose visibility fields"

os.remove(out_path)
print("Integration test PASSED")
