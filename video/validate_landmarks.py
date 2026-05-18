import json


def validate_landmarks(landmarks_path):
    with open(landmarks_path, "r") as f:
        data = json.load(f)

    total_frames = int(data.get("total_frames", 0))
    frames = data.get("frames", [])

    face_detected = 0
    pose_detected = 0
    pose_with_visibility = 0

    for frame in frames:
        face_landmarks = frame.get("face_landmarks", [])
        pose_landmarks = frame.get("pose_landmarks", [])

        if len(face_landmarks) >= 468:
            face_detected += 1

        if len(pose_landmarks) == 33:
            pose_detected += 1
            if all("visibility" in landmark for landmark in pose_landmarks):
                pose_with_visibility += 1

    face_coverage = (face_detected / total_frames) if total_frames else 0.0
    pose_coverage = (pose_detected / total_frames) if total_frames else 0.0
    pose_visibility_coverage = (pose_with_visibility / total_frames) if total_frames else 0.0

    return {
        "total_frames": total_frames,
        "face_frames": face_detected,
        "pose_frames": pose_detected,
        "pose_frames_with_visibility": pose_with_visibility,
        "face_coverage": face_coverage,
        "pose_coverage": pose_coverage,
        "pose_visibility_coverage": pose_visibility_coverage,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python validate_landmarks.py <landmarks.json>")
        raise SystemExit(1)

    report = validate_landmarks(sys.argv[1])
    print("Total frames:", report["total_frames"])
    print(
        "Face coverage: "
        f"{report['face_frames']}/{report['total_frames']} "
        f"({report['face_coverage'] * 100:.2f}%)"
    )
    print(
        "Pose coverage: "
        f"{report['pose_frames']}/{report['total_frames']} "
        f"({report['pose_coverage'] * 100:.2f}%)"
    )
    print(
        "Pose visibility coverage: "
        f"{report['pose_frames_with_visibility']}/{report['total_frames']} "
        f"({report['pose_visibility_coverage'] * 100:.2f}%)"
    )
