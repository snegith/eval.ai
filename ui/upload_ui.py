# ---------- PATH FIX ----------
import os
import sys
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

# ---------- IMPORTS ----------
import streamlit as st
import cv2
from storage.session_store import create_session, get_session_path, update_artifacts, update_metadata


def get_video_duration_seconds(video_path):
    cap = cv2.VideoCapture(video_path)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
        if fps <= 0:
            return 0.0
        return float(frame_count / fps)
    finally:
        cap.release()

st.set_page_config(page_title="Upload Interview Video", layout="centered")
st.title("📤 Upload Interview Video")

st.markdown("""
Upload a recorded interview video (MP4).

**Guidelines**
- Duration: 30 seconds – 5 minutes
- Single person visible
- Face clearly visible
- Good lighting preferred
""")

uploaded_file = st.file_uploader(
    "Choose an interview video",
    type=["mp4", "mov", "avi"]
)

if uploaded_file is not None:
    # ---------- CREATE SESSION ----------
    session_id = create_session()
    session_path = get_session_path(session_id)
    video_path = os.path.join(session_path, "video.mp4")

    # ---------- SAVE FILE ----------
    with open(video_path, "wb") as f:
        f.write(uploaded_file.read())

    duration_seconds = get_video_duration_seconds(video_path)
    update_artifacts(session_id, video=True)
    update_metadata(
        session_id,
        {
            "status": "video_uploaded",
            "duration_seconds": duration_seconds,
            "updated_at": datetime.utcnow().isoformat(),
        },
    )

    st.success("Video uploaded successfully!")
    st.code(f"Session ID: {session_id}")
    st.write("Saved at:")
    st.code(video_path)

    st.info("Next step: Run landmark extraction on this session.")
