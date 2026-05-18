import os
import sys
from pathlib import Path
from typing import List

import streamlit as st

# Ensure project root is on path (mirrors landmarks_ui behavior)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from storage.session_store import BASE_DIR as SESSIONS_BASE_DIR
from analysis.session_pipeline import run_feedback_stage, run_metrics_stage


st.set_page_config(page_title="Session Processing", layout="centered")
st.title("⚙️ Phase 3 — Session Processing")


def get_available_sessions() -> List[str]:
    """List available session directories under the configured base dir."""
    sessions_dir = Path(SESSIONS_BASE_DIR)
    if not sessions_dir.exists():
        return []
    return sorted(
        [d.name for d in sessions_dir.iterdir() if d.is_dir()],
        key=lambda name: name,
    )


sessions = get_available_sessions()

if not sessions:
    st.warning("No sessions found. Please upload a video and create a session first.")
    st.stop()


selected_session = st.selectbox(
    "Select a session to process",
    sessions,
    index=len(sessions) - 1,
)

st.info(f"Selected session: `{selected_session}`")

# Hint: Step 1 needs landmarks from Phase 2
session_path = Path(SESSIONS_BASE_DIR) / selected_session
landmarks_exists = (session_path / "landmarks.json").exists()
if not landmarks_exists:
    st.warning(
        "**Step 1 requires landmarks.** This session has no `landmarks.json`. "
        "Upload a video (Phase 1), then run **Phase 2 — Landmark Extraction** for this session before running metrics."
    )

col_metrics, col_feedback = st.columns(2)


with col_metrics:
    st.subheader("Step 1: Run Behavioral Metrics")
    st.write(
        "Run eye contact, posture, and facial animation analysis using "
        "the extracted landmarks for this session."
    )

    if st.button("Run Metrics", use_container_width=True):
        with st.spinner("Running behavioral metrics..."):
            stage_result = run_metrics_stage(selected_session)
            results = stage_result.get("metrics", {})

        # Collect actual error messages from metric results (ignore "derived" for message text)
        errors = []
        for key in ("eye_contact", "posture", "animation"):
            res = results.get(key) or {}
            if isinstance(res, dict) and res.get("error"):
                errors.append(res["error"])
        if errors:
            st.error("Metrics completed with errors: **" + errors[0] + "**")
            if len(errors) > 1 and errors[1] != errors[0]:
                st.caption("Other: " + "; ".join(errors[1:3]))
        else:
            st.success("Metrics completed successfully and saved to the session folder.")


with col_feedback:
    st.subheader("Step 2: Generate AI Feedback")
    st.write(
        "Generate structured AI feedback using the transcript (if available) "
        "and the behavioral metrics computed above."
    )

    if st.button("Generate Feedback", use_container_width=True):
        with st.spinner("Calling LLM and generating feedback..."):
            stage_result = run_feedback_stage(selected_session)
            feedback = stage_result.get("feedback", {})

        if "error" in (feedback or {}):
            st.error(f"Feedback generation failed: {feedback['error']}")
        else:
            st.success("Feedback generated successfully and saved as feedback.json.")
