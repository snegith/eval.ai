import json

import cv2
import mediapipe as mp
from google.protobuf import __version__ as PROTOBUF_VERSION


def normalize_frame(frame):
    """
    Fix portrait videos recorded with rotation metadata.
    OpenCV ignores metadata, so we rotate manually if needed.
    """
    h, w = frame.shape[:2]
    if h > w:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    return frame


def _serialize_landmarks(landmarks, include_visibility=False):
    serialized = []
    for landmark in landmarks: 
        item = {
            "x": float(landmark.x),
            "y": float(landmark.y),
            "z": float(landmark.z),
        }
        if include_visibility:
            item["visibility"] = float(getattr(landmark, "visibility", 0.0))
        serialized.append(item)
    return serialized


def _ensure_supported_runtime():
    major = int(PROTOBUF_VERSION.split(".", 1)[0])
    if major >= 5:
        raise RuntimeError(
            "Unsupported protobuf runtime detected for MediaPipe. "
            "Please run this project in the configured Python 3.11 virtual environment "
            "with protobuf<5 installed."
        )


def extract_landmarks(video_path, output_path):
    _ensure_supported_runtime()

    mp_face_mesh = mp.solutions.face_mesh
    mp_pose = mp.solutions.pose

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    frames_data = []
    frame_idx = 0

    with mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
    ) as face_mesh, mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
    ) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = normalize_frame(frame)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_result = face_mesh.process(rgb)
            pose_result = pose.process(rgb)

            frame_record = {
                "frame": frame_idx,
                "timestamp": frame_idx / fps if fps else 0.0,
                "face_landmarks": [],
                "pose_landmarks": [],
            }

            if face_result.multi_face_landmarks:
                face_landmarks = face_result.multi_face_landmarks[0].landmark
                frame_record["face_landmarks"] = _serialize_landmarks(face_landmarks)

            if pose_result.pose_landmarks:
                pose_landmarks = pose_result.pose_landmarks.landmark
                frame_record["pose_landmarks"] = _serialize_landmarks(
                    pose_landmarks,
                    include_visibility=True,
                )

            frames_data.append(frame_record)
            frame_idx += 1

    cap.release()

    with open(output_path, "w") as f:
        json.dump(
            {
                "fps": fps,
                "total_frames": frame_idx,
                "frames": frames_data,
            },
            f,
            indent=2,
        )

    return output_path
