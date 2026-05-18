import json
import numpy as np

# MediaPipe Pose indices
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_EAR = 7
RIGHT_EAR = 8


def analyze_posture(
    landmarks_path,
    torso_angle_threshold_deg=15,
    shoulder_tilt_threshold=0.15,
    visibility_threshold=0.2,
    max_fallback_ratio=0.4,
    debug=False
):

    try:
        with open(landmarks_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load landmarks file: {e}"}

    frames = data.get("frames", [])

    valid_frames = 0
    good_posture_frames = 0
    fallback_frames = 0
    hip_based_frames = 0
    skipped_visibility_count = 0

    torso_angles = []
    shoulder_tilts = []

    for frame in frames:

        pose = frame.get("pose_landmarks", [])

        if len(pose) < 25:
            continue

        # ── Check shoulder visibility (always required) ──────────────────
        try:
            shoulder_vis = min(
                pose[LEFT_SHOULDER].get("visibility", 0),
                pose[RIGHT_SHOULDER].get("visibility", 0),
            )
        except Exception:
            continue

        if shoulder_vis < visibility_threshold:
            skipped_visibility_count += 1
            continue

        # ── Extract shoulder points ──────────────────────────────────────
        try:
            ls = np.array([pose[LEFT_SHOULDER]["x"], pose[LEFT_SHOULDER]["y"]])
            rs = np.array([pose[RIGHT_SHOULDER]["x"], pose[RIGHT_SHOULDER]["y"]])
        except Exception:
            continue

        shoulder_center = (ls + rs) / 2

        # ── Hip or ear fallback for lower reference point ────────────────
        hip_vis = min(
            pose[LEFT_HIP].get("visibility", 0) if len(pose) > RIGHT_HIP else 0,
            pose[RIGHT_HIP].get("visibility", 0) if len(pose) > RIGHT_HIP else 0,
        )

        use_hip = hip_vis >= visibility_threshold
        using_fallback = False

        if use_hip:
            try:
                lh = np.array([pose[LEFT_HIP]["x"], pose[LEFT_HIP]["y"]])
                rh = np.array([pose[RIGHT_HIP]["x"], pose[RIGHT_HIP]["y"]])
                hip_center = (lh + rh) / 2
                hip_based_frames += 1
            except Exception:
                use_hip = False

        if not use_hip:
            # Fallback: use ear midpoint as upper-body vertical reference.
            # We invert the vector direction so the math stays consistent.
            try:
                le = np.array([pose[LEFT_EAR]["x"], pose[LEFT_EAR]["y"]])
                re = np.array([pose[RIGHT_EAR]["x"], pose[RIGHT_EAR]["y"]])
                hip_center = (le + re) / 2  # acts as "above-shoulder" anchor
                using_fallback = True
                fallback_frames += 1
            except Exception:
                continue

        # ── Torso angle ──────────────────────────────────────────────────
        if using_fallback:
            # Vector now points downward (shoulder → ear = upward, so flip)
            torso_vector = hip_center - shoulder_center  # ear is above shoulder
        else:
            torso_vector = shoulder_center - hip_center  # shoulder is above hip

        torso_length = np.linalg.norm(torso_vector)

        if torso_length == 0:
            continue

        vertical = np.array([0, -1])  # upward in image-space (y flipped)

        cos_angle = np.dot(torso_vector, vertical) / (
            torso_length * np.linalg.norm(vertical)
        )

        cos_angle = np.clip(cos_angle, -1, 1)
        angle_deg = np.degrees(np.arccos(cos_angle))

        # ── Shoulder tilt ────────────────────────────────────────────────
        shoulder_width = abs(rs[0] - ls[0])

        if shoulder_width == 0:
            continue

        shoulder_tilt = abs(ls[1] - rs[1]) / shoulder_width

        torso_angles.append(angle_deg)
        shoulder_tilts.append(shoulder_tilt)

        # Slightly relax angle threshold when using fallback (ear-based vector
        # naturally produces a smaller angle for the same lean)
        effective_angle_threshold = (
            torso_angle_threshold_deg * 0.6 if using_fallback else torso_angle_threshold_deg
        )

        if angle_deg < effective_angle_threshold and shoulder_tilt < shoulder_tilt_threshold:
            good_posture_frames += 1

        valid_frames += 1

        if debug:
            print(
                f"Frame {frame.get('frame', '?')} | "
                f"angle={angle_deg:.1f}° | "
                f"tilt={shoulder_tilt:.4f} | "
                f"fallback={using_fallback}"
            )

    if valid_frames == 0 or len(torso_angles) == 0:
        return {
            "error": "No valid posture frames detected",
            "debug_info": {
                "total_frames": len(frames),
                "skipped_low_visibility": skipped_visibility_count,
                "tip": (
                    "Hips were not visible in enough frames and ear fallback also failed. "
                    "Ensure shoulders and ideally upper torso are in frame."
                ),
            },
        }

    fallback_ratio = fallback_frames / valid_frames if valid_frames else 1.0
    if hip_based_frames == 0 or fallback_ratio > max_fallback_ratio:
        return {
            "error": "Insufficient hip visibility for reliable posture scoring",
            "debug_info": {
                "total_frames": len(frames),
                "valid_frames": valid_frames,
                "hip_based_frames": hip_based_frames,
                "fallback_frames": fallback_frames,
                "fallback_ratio": round(fallback_ratio, 3),
                "skipped_low_visibility": skipped_visibility_count,
                "tip": (
                    "Keep both shoulders and upper torso in frame so hip landmarks are "
                    "visible often enough for a reliable posture score."
                ),
            },
        }

    posture_pct = (good_posture_frames / valid_frames) * 100

    if posture_pct >= 80:
        grade = "Excellent"
    elif posture_pct >= 65:
        grade = "Good"
    elif posture_pct >= 50:
        grade = "Fair"
    elif posture_pct >= 30:
        grade = "Needs Improvement"
    else:
        grade = "Poor"

    return {
        "posture_percentage": round(posture_pct, 2),
        "posture_score": round(posture_pct, 0),
        "grade": grade,
        "mean_torso_angle_deg": round(float(np.mean(torso_angles)), 2),
        "max_torso_angle_deg": round(float(np.max(torso_angles)), 2),
        "mean_shoulder_tilt": round(float(np.mean(shoulder_tilts)), 4),
        "max_shoulder_tilt": round(float(np.max(shoulder_tilts)), 4),
        "valid_frames": valid_frames,
        "total_frames": len(frames),
        "hip_based_frames": hip_based_frames,
        "fallback_frames": fallback_frames,
        "fallback_used": fallback_frames > 0,
        "skipped_low_visibility": skipped_visibility_count,
    }


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python posture.py <pose_landmarks.json> [--debug]")
        sys.exit(1)

    path = sys.argv[1]
    debug = "--debug" in sys.argv

    result = analyze_posture(path, debug=debug)

    if "error" in result:
        print(f"ERROR: {result['error']}")
        if "debug_info" in result:
            print(f"DEBUG: {result['debug_info']}")
    else:
        print(f"\nPosture Score:     {result['posture_score']}/100 ({result['grade']})")
        print(f"Mean Torso Angle:  {result['mean_torso_angle_deg']}°")
        print(f"Mean Shoulder Tilt:{result['mean_shoulder_tilt']}")
        print(f"Valid Frames:      {result['valid_frames']} / {result['total_frames']}")
        if result["fallback_used"]:
            print(
                f"⚠️  Ear fallback used for {result['fallback_frames']} frames "
                f"(hips not visible — consider framing upper torso in shot)"
            )
