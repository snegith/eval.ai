import os
import sys
from pathlib import Path

import streamlit as st

# Ensure project root is on path (mirrors other UI pages)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from storage.session_store import (
    BASE_DIR as SESSIONS_BASE_DIR,
    get_session_path,
    resolve_video_path,
    save_json,
    update_artifacts,
    update_metadata,
)


st.set_page_config(page_title="Audio + Transcript", layout="centered")
st.title("🗣️ Phase 1 — Audio Intelligence (Transcript + Metrics)")

st.caption(
    "This step extracts audio from `video.mp4`, transcribes it with Whisper, "
    "computes basic speech metrics, and saves `transcript.json` in the session folder."
)


def get_sessions_with_video() -> list[str]:
    sessions_dir = Path(SESSIONS_BASE_DIR)
    if not sessions_dir.exists():
        return []
    sessions = []
    for d in sessions_dir.iterdir():
        if not d.is_dir():
            continue
        if resolve_video_path(d.name):
            sessions.append(d.name)
    return sorted(sessions)


sessions = get_sessions_with_video()
if not sessions:
    st.warning("No sessions with video.mp4 found. Upload a video first.")
    st.stop()

session_id = st.selectbox("Select a session", sessions, index=len(sessions) - 1)
session_path = Path(get_session_path(session_id))

resolved_video_path = resolve_video_path(session_id)
video_path = Path(resolved_video_path) if resolved_video_path else session_path / "video.mp4"
audio_path = session_path / "audio.wav"

col1, col2 = st.columns(2)
with col1:
    model_name = st.selectbox("Whisper model", ["tiny", "base", "small"], index=1)
with col2:
    pause_threshold = st.number_input("Long pause threshold (sec)", min_value=0.5, max_value=10.0, value=2.0, step=0.5)


if st.button("Extract + Transcribe", use_container_width=True):
    if not video_path.exists():
        st.error(f"Missing video file: `{video_path}`")
        st.stop()

    try:
        # Import here so the page can still load even if optional deps
        # (moviepy/whisper) are not installed yet.
        from audio.extract import extract_audio
        from audio.transcription import transcribe
        from audio.pace import speaking_pace
        from audio.fillers import count_fillers
        from audio.pauses import detect_pauses

        with st.spinner("Extracting audio..."):
            # Ensure parent exists (session folder should, but be defensive)
            session_path.mkdir(parents=True, exist_ok=True)
            extracted_audio = extract_audio(str(video_path), audio_path=str(audio_path))

        with st.spinner("Transcribing with Whisper (may take a while)..."):
            transcript_text, segments = transcribe(extracted_audio, model_name=model_name)

        # Duration estimate from segments if available
        duration_sec = 0.0
        try:
            if segments:
                duration_sec = float(segments[-1].get("end", 0.0))
        except Exception:
            duration_sec = 0.0

        with st.spinner("Computing speech metrics..."):
            wpm = speaking_pace(transcript_text, max(duration_sec, 1.0))
            filler_counts = count_fillers(transcript_text)
            pauses = detect_pauses(segments, threshold=float(pause_threshold))

        transcript_payload = {
            "language": "unknown",
            "duration_sec": duration_sec,
            "full_text": transcript_text,
            "segments": segments,
        }
        save_json(session_id, "transcript.json", transcript_payload)

        audio_metrics_payload = {
            "duration_sec": duration_sec,
            "wpm": wpm,
            "fillers": filler_counts,
            "long_pauses_count": len(pauses),
            "pause_threshold_sec": float(pause_threshold),
            "model": model_name,
            "files": {
                "video": "video.mp4",
                "audio": "audio.wav",
                "transcript": "transcript.json",
            },
        }
        save_json(session_id, "audio_metrics.json", audio_metrics_payload)
        update_artifacts(session_id, audio=True, transcript=True)
        update_metadata(
            session_id,
            {
                "status": "audio_processed",
                "duration_seconds": max(float(duration_sec), float(audio_metrics_payload["duration_sec"])),
            },
        )

        st.success("Transcript + audio metrics saved to session.")

        st.subheader("Transcript (preview)")
        st.text_area("Transcript", transcript_text, height=200)

        st.subheader("Speech metrics")
        st.metric("Speaking pace (WPM)", wpm)
        st.metric("Long pauses", len(pauses))
        st.write("Filler word counts")
        st.json(filler_counts)

    except ModuleNotFoundError as e:
        st.error(f"Missing dependency: {e}.")
        st.code("pip install -r requirements.txt")
        st.info("You may also need ffmpeg installed for moviepy/whisper to work.")
    except Exception as e:
        st.error(f"Audio/transcription failed: {e}")

