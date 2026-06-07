"""Sanity check for MediaPipe FaceMesh on a sample interview frame."""
import os

import cv2
import pytest

from tests.conftest import mediapipe_runtime_ready

VIDEO_PATH = os.environ.get(
    "FACE_MESH_TEST_VIDEO",
    "data/sessions/session_763c54f7/video.mp4",
)


@pytest.mark.skipif(
    not mediapipe_runtime_ready(),
    reason="MediaPipe requires protobuf<5 in a Python 3.11 virtual environment",
)
@pytest.mark.skipif(
    not os.path.exists(VIDEO_PATH),
    reason=f"Test video not found at {VIDEO_PATH}",
)
def test_face_mesh_detects_face_in_sample_frame():
    import mediapipe as mp

    cap = cv2.VideoCapture(VIDEO_PATH)
    ret, frame = cap.read()
    cap.release()

    assert ret, "Failed to read a frame from the test video"
    assert frame is not None

    mp_face = mp.solutions.face_mesh
    with mp_face.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
    ) as face_mesh:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)

        rotations = {
            "raw": frame,
            "90_cw": cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE),
            "90_ccw": cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE),
            "180": cv2.rotate(frame, cv2.ROTATE_180),
        }

        detected_orientations = []
        for name, rotated in rotations.items():
            rgb_rotated = cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB)
            rotated_result = face_mesh.process(rgb_rotated)
            if rotated_result.multi_face_landmarks:
                detected_orientations.append(name)

    assert result.multi_face_landmarks or detected_orientations, (
        "FaceMesh did not detect a face in the raw frame or common rotations"
    )
