TRANSCRIPT_SCHEMA = {
    # Language code for the transcript (ISO 639-1)
    "language": "en",
    # Total duration of the interview in seconds
    "duration_sec": 0.0,
    # Full transcript text used for LLM feedback
    "full_text": "",
    # Optional segmented transcript for future analysis
    "segments": [
        {
            "start_sec": 0.0,
            "end_sec": 0.0,
            "speaker": "candidate",
            "text": ""
        }
    ],
}

METADATA_SCHEMA = {
    "session_id": "",
    "created_at": "",
    "updated_at": "",
    "status": "initialized",
    "schema_version": "1.0",
    "video_filename": "video.mp4",
    "resume_filename": "",
    "duration_seconds": 0.0,
    "last_error": "",
    "artifacts": {
        "video": False,
        "resume": False,
        "resume_text": False,
        "resume_profile": False,
        "resume_review": False,
        "questions": False,
        "audio": False,
        "transcript": False,
        "landmarks": False,
        "eye_contact": False,
        "posture": False,
        "animation": False,
        "derived": False,
        "feedback": False,
    },
}

# Canonical structure for per-frame landmarks as written by video/landmarks.py
LANDMARK_SCHEMA = {
    "fps": 0.0,
    "total_frames": 0,
    "frames": [
        {
            "frame": 0,
            "timestamp": 0.0,
            "face_landmarks": [
                {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                }
            ],
            "pose_landmarks": [
                {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "visibility": 0.0,
                }
            ],
        }
    ],
}

# High-level summary schema for a fully analyzed session.
# This is illustrative and not strictly enforced at runtime, but it
# reflects the JSON shapes produced in each phase.
ANALYSIS_SCHEMA = {
    "session_id": "",
    "metadata": METADATA_SCHEMA,
    "landmarks": LANDMARK_SCHEMA,
    "eye_contact": {
        "total_frames": 0,
        "looking_frames": 0,
        "skipped_frames": 0,
        "eye_contact_percentage": 0.0,
        "eye_contact_score": 0.0,
        "grade": "",
        "longest_streak": 0,
        "gaze_stability": 0.0,
        # Optional diagnostic blocks
        "gaze_stats": {},
        "thresholds_used": {},
        "error": "",
    },
    "posture": {
        "posture_percentage": 0.0,
        "posture_score": 0.0,
        "grade": "",
        "mean_torso_angle_deg": 0.0,
        "max_torso_angle_deg": 0.0,
        "mean_shoulder_tilt": 0.0,
        "max_shoulder_tilt": 0.0,
        "valid_frames": 0,
        "total_frames": 0,
        "hip_based_frames": 0,
        "fallback_frames": 0,
        "fallback_used": False,
        "error": "",
    },
    "animation": {
        "total_frames": 0,
        "valid_frames": 0,
        "expressiveness_score": 0.0,
        "consistency_score": 0.0,
        "stability_score": 0.0,
        "grade": "",
        "animation_metrics": {},
        "expression_dynamics": {},
        "raw_statistics": {},
        "error": "",
    },
    "feedback": {
        "overall_score": 0,
        "score_breakdown": {
            "content": 0,
            "eye_contact": 0,
            "posture": 0,
            "animation": 0,
        },
        "strengths": [],
        "improvements": [],
        "recommendations": [],
        "summary": "",
        "star_analysis": {
            "applicable": False,
            "situation_score": None,
            "task_score": None,
            "action_score": None,
            "result_score": None,
            "overall_star_score": None,
            "feedback": "",
        },
        "_metadata": {
            "model": "",
            "temperature": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "attempt": 0,
        },
    },
    # Derived high-level behavioral indicators
    "derived": {
        "confidence_score": 0.0,
        "nervousness_score": 0.0,
        "source_metrics": {},
        "weights": {},
    },
}
