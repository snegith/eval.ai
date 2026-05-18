import json
import numpy as np
from pathlib import Path
from config import CONFIG

# MediaPipe indices
LEFT_EYE_CORNER = 33
RIGHT_EYE_CORNER = 263
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

LEFT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380]


def mean_point(landmarks, indices):
    pts = np.array([[landmarks[i]["x"], landmarks[i]["y"]] for i in indices])
    return pts.mean(axis=0)


def get_eye_center_fallback(landmarks, eye_landmarks):
    try:
        return mean_point(landmarks, eye_landmarks)
    except Exception:
        return None


def analyze_eye_contact(
    landmarks_path,
    threshold_x=CONFIG["eye_threshold_x"],
    threshold_y=CONFIG["eye_threshold_y"],
    use_smoothing=True,
    smoothing_window=CONFIG["eye_smoothing_window"],
    debug=False
):

    try:
        with open(landmarks_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        return {
            "error": str(e),
            "total_frames": 0,
            "looking_frames": 0,
            "eye_contact_percentage": 0.0,
        }

    frames = data.get("frames", [])
    if not frames:
        return {
            "error": "No frames found",
            "total_frames": 0,
            "looking_frames": 0,
            "eye_contact_percentage": 0.0,
        }

    total_frames = 0
    looking_frames = 0
    skipped_frames = 0

    gaze_x_vals = []
    gaze_y_vals = []
    gaze_mag_vals = []
    looking_flags = []

    gaze_buffer_x = []
    gaze_buffer_y = []

    for frame in frames:

        face = frame.get("face_landmarks", [])

        if len(face) < 468:
            skipped_frames += 1
            continue

        try:
            left_iris = mean_point(face, LEFT_IRIS)
            right_iris = mean_point(face, RIGHT_IRIS)
            eye_center = (left_iris + right_iris) / 2
        except Exception:

            left_eye = get_eye_center_fallback(face, LEFT_EYE_LANDMARKS)
            right_eye = get_eye_center_fallback(face, RIGHT_EYE_LANDMARKS)

            if left_eye is None or right_eye is None:
                skipped_frames += 1
                continue

            eye_center = (left_eye + right_eye) / 2

        try:
            left_eye_corner = np.array([face[LEFT_EYE_CORNER]["x"], face[LEFT_EYE_CORNER]["y"]])
            right_eye_corner = np.array([face[RIGHT_EYE_CORNER]["x"], face[RIGHT_EYE_CORNER]["y"]])
        except Exception:
            skipped_frames += 1
            continue

        face_center = (left_eye_corner + right_eye_corner) / 2
        eye_width = abs(right_eye_corner[0] - left_eye_corner[0])
        eye_height = eye_width * 0.3

        if eye_width == 0 or eye_height == 0:
            skipped_frames += 1
            continue

        gaze_x = abs(eye_center[0] - face_center[0]) / eye_width
        gaze_y = abs(eye_center[1] - face_center[1]) / eye_height

        if use_smoothing:

            gaze_buffer_x.append(gaze_x)
            gaze_buffer_y.append(gaze_y)

            if len(gaze_buffer_x) > smoothing_window:
                gaze_buffer_x.pop(0)
                gaze_buffer_y.pop(0)

            gaze_x_s = np.mean(gaze_buffer_x)
            gaze_y_s = np.mean(gaze_buffer_y)

        else:
            gaze_x_s = gaze_x
            gaze_y_s = gaze_y

        gaze_mag = np.hypot(gaze_x_s, gaze_y_s)

        is_looking = (gaze_x_s < threshold_x) and (gaze_y_s < threshold_y)

        gaze_x_vals.append(gaze_x_s)
        gaze_y_vals.append(gaze_y_s)
        gaze_mag_vals.append(gaze_mag)
        looking_flags.append(is_looking)

        if is_looking:
            looking_frames += 1

        total_frames += 1

    if total_frames == 0:
        return {
            "error": "No valid gaze frames",
            "total_frames": 0,
            "looking_frames": 0,
            "eye_contact_percentage": 0.0,
        }

    gaze_x_array = np.array(gaze_x_vals)
    gaze_y_array = np.array(gaze_y_vals)
    gaze_mag_array = np.array(gaze_mag_vals)

    eye_contact_pct = (looking_frames / total_frames) * 100

    longest_streak = 0
    current = 0

    for flag in looking_flags:
        if flag:
            current += 1
            longest_streak = max(longest_streak, current)
        else:
            current = 0

    gaze_stability = 1 - (np.std(gaze_mag_array) / (np.mean(gaze_mag_array) + 1e-6))
    gaze_stability = max(0, min(1, gaze_stability))

    if eye_contact_pct >= 80:
        grade = "Excellent"
    elif eye_contact_pct >= 65:
        grade = "Good"
    elif eye_contact_pct >= 50:
        grade = "Fair"
    elif eye_contact_pct >= 30:
        grade = "Needs Improvement"
    else:
        grade = "Poor"

    return {
        "total_frames": total_frames,
        "looking_frames": looking_frames,
        "skipped_frames": skipped_frames,
        "eye_contact_percentage": round(eye_contact_pct, 2),
        "eye_contact_score": round(eye_contact_pct, 0),
        "grade": grade,
        "longest_streak": longest_streak,
        "gaze_stability": round(gaze_stability, 3),
        "gaze_stats": {
            "horizontal": {
                "mean": float(gaze_x_array.mean()),
                "max": float(gaze_x_array.max()),
                "std": float(gaze_x_array.std()),
            },
            "vertical": {
                "mean": float(gaze_y_array.mean()),
                "max": float(gaze_y_array.max()),
                "std": float(gaze_y_array.std()),
            },
        },
        "thresholds_used": {
            "horizontal": threshold_x,
            "vertical": threshold_y,
        }
    }
