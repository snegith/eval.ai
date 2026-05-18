# ---------- PATH FIX ----------
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

import streamlit as st
from video.landmarks import extract_landmarks
from video.validate_landmarks import validate_landmarks
from storage.session_store import (
    BASE_DIR as SESSIONS_DIR,
    resolve_video_path,
    update_artifacts,
    update_metadata,
)

st.set_page_config(page_title="Landmark Extraction", layout="centered")
st.title("🧠 Phase 2A — Landmark Extraction")

# ---------- FIND VALID SESSIONS ----------
sessions = []
if os.path.exists(SESSIONS_DIR):
    for s in os.listdir(SESSIONS_DIR):
        video_path = resolve_video_path(s)
        if video_path:
            sessions.append(s)

if not sessions:
    st.warning("No recorded sessions with video.mp4 found.")
    st.stop()

# ---------- SESSION SELECT ----------
session_id = st.selectbox(
    "Select a session to analyze",
    sessions,
    index=len(sessions) - 1  # default to latest
)

session_path = os.path.join(SESSIONS_DIR, session_id)
video_path = resolve_video_path(session_id) or os.path.join(session_path, "video.mp4")
output_path = os.path.join(session_path, "landmarks.json")

st.success(f"Using session: {session_id}")

# ---------- RUN EXTRACTION ----------
if st.button("Run Landmark Extraction"):
    try:
        with st.spinner("Extracting face & pose landmarks..."):
            extract_landmarks(video_path, output_path)
            report = validate_landmarks(output_path)

        st.success("Landmarks extracted successfully.")
        st.write(f"Saved to: `{output_path}`")
        st.write(
            f"Face coverage: {report['face_coverage'] * 100:.1f}% | "
            f"Pose coverage: {report['pose_coverage'] * 100:.1f}%"
        )
        update_artifacts(session_id, landmarks=True)
        update_metadata(session_id, {"status": "landmarks_extracted"})

        if report["face_coverage"] <= 0.0:
            st.error("No usable FaceMesh frames were detected. Downstream eye and animation metrics will fail.")
        if report["pose_visibility_coverage"] <= 0.0:
            st.error("No usable pose frames with visibility were detected. Downstream posture analysis will fail.")
    except Exception as e:
        st.error(f"Landmark extraction failed: {e}")
