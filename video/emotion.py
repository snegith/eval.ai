import json
import numpy as np

# Face landmark indices (MediaPipe)
UPPER_LIP = 13
LOWER_LIP = 14
LEFT_EYE_TOP = 159
LEFT_EYE_BOTTOM = 145
RIGHT_EYE_TOP = 386
RIGHT_EYE_BOTTOM = 374
LEFT_BROW = 70
RIGHT_BROW = 300
NOSE_TIP = 1


def distance(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))


def analyze_emotion(landmarks_path, debug=False):
    with open(landmarks_path, "r") as f:
        data = json.load(f)

    frames = data["frames"]

    mouth_open_vals = []
    eye_open_vals = []
    brow_raise_vals = []

    for frame in frames:
        face = frame.get("face_landmarks", [])
        if len(face) < 468:
            continue

        # Mouth openness
        mouth_open = distance(
            [face[UPPER_LIP]["x"], face[UPPER_LIP]["y"]],
            [face[LOWER_LIP]["x"], face[LOWER_LIP]["y"]],
        )

        # Eye openness (average of both eyes)
        left_eye = distance(
            [face[LEFT_EYE_TOP]["x"], face[LEFT_EYE_TOP]["y"]],
            [face[LEFT_EYE_BOTTOM]["x"], face[LEFT_EYE_BOTTOM]["y"]],
        )
        right_eye = distance(
            [face[RIGHT_EYE_TOP]["x"], face[RIGHT_EYE_TOP]["y"]],
            [face[RIGHT_EYE_BOTTOM]["x"], face[RIGHT_EYE_BOTTOM]["y"]],
        )
        eye_open = (left_eye + right_eye) / 2

        # Brow raise (brow to nose)
        brow_raise = distance(
            [face[LEFT_BROW]["x"], face[LEFT_BROW]["y"]],
            [face[NOSE_TIP]["x"], face[NOSE_TIP]["y"]],
        )

        mouth_open_vals.append(mouth_open)
        eye_open_vals.append(eye_open)
        brow_raise_vals.append(brow_raise)

    if not mouth_open_vals:
        return {"error": "No valid face frames found"}

    # Convert to arrays
    mouth = np.array(mouth_open_vals)
    eye = np.array(eye_open_vals)
    brow = np.array(brow_raise_vals)

    result = {
        "mouth_open_mean": float(mouth.mean()),
        "mouth_open_std": float(mouth.std()),
        "eye_open_mean": float(eye.mean()),
        "eye_open_std": float(eye.std()),
        "brow_raise_mean": float(brow.mean()),
        "brow_raise_std": float(brow.std()),
    }

    if debug:
        print("\nEMOTION DEBUG")
        print("-" * 40)
        for k, v in result.items():
            print(f"{k}: {v:.4f}")

    return result
