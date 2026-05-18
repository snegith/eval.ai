import json
import numpy as np
from scipy import signal
from config import CONFIG

# MediaPipe Face Mesh landmark indices
MOUTH_TOP = 13
MOUTH_BOTTOM = 14
LEFT_EYE_TOP = 159
LEFT_EYE_BOTTOM = 145
RIGHT_EYE_TOP = 386
RIGHT_EYE_BOTTOM = 374
LEFT_BROW = 70
RIGHT_BROW = 300
NOSE_TIP = 1


def sliding_window_std(arr, window):
    """Calculate standard deviation over sliding windows."""
    stds = []
    for i in range(len(arr) - window + 1):
        stds.append(np.std(arr[i:i + window]))
    return stds


def detect_peaks(signal_array, prominence_factor=0.5):
    """Detect significant peaks in a signal with adaptive prominence."""
    if len(signal_array) < 3:
        return []
    
    # Adaptive prominence based on signal's own statistics
    adaptive_prominence = prominence_factor * np.std(signal_array)
    
    peaks, properties = signal.find_peaks(
        signal_array,
        prominence=adaptive_prominence
    )
    return peaks


def normalize_feature(feature_array):
    """Normalize feature to 0-1 range."""
    feature_array = np.array(feature_array)
    min_val = np.min(feature_array)
    max_val = np.max(feature_array)
    if max_val - min_val < 1e-6:
        return np.zeros_like(feature_array)
    return (feature_array - min_val) / (max_val - min_val)


def analyze_facial_animation(
    landmarks_path,
    window_size=CONFIG["animation_window_size"],        # ~1 second at 30fps
    debug=False
):
    """
    Analyze facial animation dynamics (NOT emotion classification).
    
    Measures:
    - Facial expressiveness (how animated)
    - Mouth animation (talking/smiling intensity)
    - Eye animation (engagement indicators)
    - Expression variability (consistency)
    
    NOTE: This does NOT classify emotions (happy/sad/angry).
    For true emotion detection, use a trained emotion recognition model.
    """
    
    try:
        with open(landmarks_path, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return {"error": str(e)}
    
    frames = data.get("frames", [])
    if not frames:
        return {"error": "No frames found"}
    
    # Raw feature arrays
    mouth_openness = []
    eye_openness = []
    brow_raise = []
    valid_frames = 0
    
    for frame in frames:
        face = frame.get("face_landmarks", [])
        
        # FaceMesh does NOT have visibility - just check landmark count
        if len(face) < 468:
            continue
        
        try:
            # Mouth openness (vertical distance)
            mouth_val = abs(face[MOUTH_TOP]["y"] - face[MOUTH_BOTTOM]["y"])
            mouth_openness.append(mouth_val)
            
            # Eye openness (average of both eyes)
            left_eye_val = abs(face[LEFT_EYE_TOP]["y"] - face[LEFT_EYE_BOTTOM]["y"])
            right_eye_val = abs(face[RIGHT_EYE_TOP]["y"] - face[RIGHT_EYE_BOTTOM]["y"])
            eye_val = (left_eye_val + right_eye_val) / 2
            eye_openness.append(eye_val)
            
            # Brow raise (distance from brow to nose)
            left_brow_val = abs(face[LEFT_BROW]["y"] - face[NOSE_TIP]["y"])
            right_brow_val = abs(face[RIGHT_BROW]["y"] - face[NOSE_TIP]["y"])
            brow_val = (left_brow_val + right_brow_val) / 2
            brow_raise.append(brow_val)
            
            valid_frames += 1
            
        except (KeyError, IndexError, TypeError):
            continue
    
    if valid_frames < window_size:
        return {
            "error": f"Insufficient valid frames: {valid_frames} (need at least {window_size})"
        }
    
    # Convert to numpy arrays
    mouth_openness = np.array(mouth_openness)
    eye_openness = np.array(eye_openness)
    brow_raise = np.array(brow_raise)
    
    # Normalize features (0-1 scale)
    mouth_norm = normalize_feature(mouth_openness)
    eye_norm = normalize_feature(eye_openness)
    brow_norm = normalize_feature(brow_raise)
    
    # Calculate variability (standard deviation over windows)
    mouth_variability = sliding_window_std(mouth_norm, window_size)
    eye_variability = sliding_window_std(eye_norm, window_size)
    brow_variability = sliding_window_std(brow_norm, window_size)
    
    # Overall animation intensity (mean of normalized features)
    animation_intensity = (mouth_norm + eye_norm + brow_norm) / 3
    
    # Smooth animation intensity for trend analysis
    if len(animation_intensity) >= window_size:
        animation_smooth = np.convolve(
            animation_intensity,
            np.ones(window_size) / window_size,
            mode='valid'
        )
    else:
        animation_smooth = animation_intensity
    
    # Detect animation peaks with adaptive prominence
    peaks = detect_peaks(animation_smooth, prominence_factor=0.5)
    
    # Calculate metrics
    
    # 1. Overall expressiveness (0-100 scale)
    expressiveness_score = np.mean(animation_intensity) * 100
    
    # 2. Animation consistency (inverse of variability) - FIXED
    variability_mean = np.mean([
        np.mean(mouth_variability),
        np.mean(eye_variability),
        np.mean(brow_variability)
    ])
    
    # Normalize consistency score properly (no magic numbers)
    # Typical variability range is 0-0.5, so we scale by 2
    consistency_score = 100 * (1 - np.clip(variability_mean * 2, 0, 1))
    
    # 3. Engagement indicators
    mouth_activity = np.mean(mouth_variability) * 100  # Talking/smiling
    eye_activity = np.mean(eye_variability) * 100      # Attention shifts
    
    # 4. Expression dynamics
    expression_peaks = len(peaks)  # Number of expressive moments
    peak_frequency = expression_peaks / (len(animation_smooth) / 30) if len(animation_smooth) > 0 else 0
    
    # 5. Temporal stability
    stability_score = 100 - (np.std(animation_smooth) * 100)
    stability_score = max(0, min(100, stability_score))
    
    # Grade overall facial animation
    # Consider BOTH expressiveness AND consistency
    if expressiveness_score >= 60 and consistency_score >= 60:
        grade = "Excellent - Highly Expressive & Consistent"
    elif expressiveness_score >= 60 and consistency_score < 50:
        grade = "Good - Expressive but Variable (possible nervousness)"
    elif expressiveness_score >= 45 and consistency_score >= 50:
        grade = "Good - Well Animated"
    elif expressiveness_score >= 30:
        grade = "Fair - Moderately Expressive"
    elif expressiveness_score >= 20:
        grade = "Limited - Low Animation"
    else:
        grade = "Very Limited - Minimal Expression"
    
    result = {
        "total_frames": len(frames),
        "valid_frames": valid_frames,
        "expressiveness_score": round(expressiveness_score, 2),
        "consistency_score": round(consistency_score, 2),
        "stability_score": round(stability_score, 2),
        "grade": grade,
        "animation_metrics": {
            "mouth_activity": round(mouth_activity, 2),
            "eye_activity": round(eye_activity, 2),
            "brow_activity": round(np.mean(brow_variability) * 100, 2),
        },
        "expression_dynamics": {
            "peak_count": int(expression_peaks),
            "peak_frequency_per_sec": round(peak_frequency, 2),
            "animation_range": {
                "min": round(float(np.min(animation_intensity)) * 100, 2),
                "mean": round(float(np.mean(animation_intensity)) * 100, 2),
                "max": round(float(np.max(animation_intensity)) * 100, 2),
            }
        },
        "raw_statistics": {
            "mouth": {
                "mean": round(float(np.mean(mouth_norm)), 4),
                "std": round(float(np.std(mouth_norm)), 4),
            },
            "eyes": {
                "mean": round(float(np.mean(eye_norm)), 4),
                "std": round(float(np.std(eye_norm)), 4),
            },
            "brows": {
                "mean": round(float(np.mean(brow_norm)), 4),
                "std": round(float(np.std(brow_norm)), 4),
            }
        }
    }
    
    if debug:
        print("\n" + "="*60)
        print("FACIAL ANIMATION ANALYSIS DEBUG")
        print("="*60)
        print(f"Total frames: {len(frames)}")
        print(f"Valid frames: {valid_frames}")
        print(f"\nExpressiveness Score: {expressiveness_score:.2f}/100")
        print(f"Consistency Score: {consistency_score:.2f}/100")
        print(f"Stability Score: {stability_score:.2f}/100")
        print(f"Variability Mean: {variability_mean:.4f}")
        print(f"\nAnimation Metrics:")
        print(f"  Mouth activity: {mouth_activity:.2f}")
        print(f"  Eye activity: {eye_activity:.2f}")
        print(f"  Brow activity: {result['animation_metrics']['brow_activity']:.2f}")
        print(f"\nExpression Dynamics:")
        print(f"  Expressive moments: {expression_peaks}")
        print(f"  Peak frequency: {peak_frequency:.2f}/sec")
        print(f"\nGrade: {grade}")
        print("="*60)
        print("\n⚠️  NOTE: This measures facial ANIMATION, not emotions.")
        print("For true emotion detection, use a trained emotion recognition model.")
        print("="*60 + "\n")
    
    return result


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python facial_animation.py <face_landmarks.json> [--debug]")
        sys.exit(1)
    
    path = sys.argv[1]
    debug = "--debug" in sys.argv
    
    result = analyze_facial_animation(path, debug=debug)
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
    else:
        print(f"\nFacial Animation Score: {result['expressiveness_score']:.2f}/100")
        print(f"Grade: {result['grade']}")
        print(f"\nKey Metrics:")
        print(f"  Expressiveness: {result['expressiveness_score']:.2f}")
        print(f"  Consistency: {result['consistency_score']:.2f}")
        print(f"  Stability: {result['stability_score']:.2f}")
        
        if not debug:
            print("\nFull results:")
            print(json.dumps(result, indent=2))
