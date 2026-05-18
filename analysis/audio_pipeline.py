from pathlib import Path
from typing import Any, Dict

from audio.fillers import count_fillers
from audio.pace import speaking_pace
from audio.pauses import detect_pauses
from storage.session_store import (
    get_session_path,
    resolve_video_path,
    save_json,
    update_artifacts,
    update_metadata,
)


def run_audio_for_session(
    session_id: str,
    model_name: str = "base",
    pause_threshold: float = 2.0,
) -> Dict[str, Any]:
    session_path = Path(get_session_path(session_id))
    session_path.mkdir(parents=True, exist_ok=True)

    video_path = resolve_video_path(session_id)
    if not video_path:
        error = f"No video file found for session {session_id}"
        update_metadata(session_id, {"status": "audio_failed", "last_error": error})
        return {"error": error}

    audio_path = session_path / "audio.wav"

    try:
        from audio.extract import extract_audio
        from audio.transcription import transcribe
    except Exception as exc:
        error = f"Audio pipeline dependency missing: {exc}"
        transcript_payload = {
            "language": "unknown",
            "duration_sec": 0.0,
            "full_text": "",
            "segments": [],
            "error": error,
        }
        audio_metrics_payload = {
            "duration_sec": 0.0,
            "wpm": 0.0,
            "fillers": {},
            "long_pauses_count": 0,
            "pause_threshold_sec": float(pause_threshold),
            "model": model_name,
            "error": error,
            "files": {
                "video": Path(video_path).name,
                "audio": "audio.wav",
                "transcript": "transcript.json",
            },
        }
        save_json(session_id, "transcript.json", transcript_payload)
        save_json(session_id, "audio_metrics.json", audio_metrics_payload)
        update_artifacts(session_id, audio=False, transcript=False)
        update_metadata(
            session_id,
            {
                "status": "audio_skipped",
                "last_error": error,
            },
        )
        return {
            "error": error,
            "transcript": transcript_payload,
            "audio_metrics": audio_metrics_payload,
        }

    try:
        extracted_audio = extract_audio(video_path, audio_path=str(audio_path))
        transcript_text, segments = transcribe(extracted_audio, model_name=model_name)
    except Exception as exc:
        error = f"Audio processing unavailable: {exc}"
        transcript_payload = {
            "language": "unknown",
            "duration_sec": 0.0,
            "full_text": "",
            "segments": [],
            "error": error,
        }
        audio_metrics_payload = {
            "duration_sec": 0.0,
            "wpm": 0.0,
            "fillers": {},
            "long_pauses_count": 0,
            "pause_threshold_sec": float(pause_threshold),
            "model": model_name,
            "error": error,
            "files": {
                "video": Path(video_path).name,
                "audio": "audio.wav",
                "transcript": "transcript.json",
            },
        }
        save_json(session_id, "transcript.json", transcript_payload)
        save_json(session_id, "audio_metrics.json", audio_metrics_payload)
        update_artifacts(session_id, audio=False, transcript=False)
        update_metadata(
            session_id,
            {
                "status": "audio_skipped",
                "last_error": error,
            },
        )
        return {
            "error": error,
            "transcript": transcript_payload,
            "audio_metrics": audio_metrics_payload,
        }

    duration_sec = 0.0
    if segments:
        try:
            duration_sec = float(segments[-1].get("end", 0.0))
        except Exception:
            duration_sec = 0.0

    wpm = speaking_pace(transcript_text, max(duration_sec, 1.0))
    filler_counts = count_fillers(transcript_text)
    pauses = detect_pauses(segments, threshold=float(pause_threshold))

    transcript_payload = {
        "language": "unknown",
        "duration_sec": duration_sec,
        "full_text": transcript_text,
        "segments": segments,
    }
    audio_metrics_payload = {
        "duration_sec": duration_sec,
        "wpm": wpm,
        "fillers": filler_counts,
        "long_pauses_count": len(pauses),
        "pause_threshold_sec": float(pause_threshold),
        "model": model_name,
        "files": {
            "video": Path(video_path).name,
            "audio": "audio.wav",
            "transcript": "transcript.json",
        },
    }

    save_json(session_id, "transcript.json", transcript_payload)
    save_json(session_id, "audio_metrics.json", audio_metrics_payload)
    update_artifacts(session_id, audio=True, transcript=True)
    update_metadata(
        session_id,
        {
            "status": "audio_processed",
            "duration_seconds": max(float(duration_sec), float(audio_metrics_payload["duration_sec"])),
            "last_error": "",
        },
    )

    return {
        "transcript": transcript_payload,
        "audio_metrics": audio_metrics_payload,
    }
