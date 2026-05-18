import os
import sys

import streamlit as st

# Ensure project root is on path (mirrors ui/* pages)
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


st.set_page_config(page_title="AI Interview Evaluator", layout="centered")
st.title("AI Interview Evaluation — Runner")

st.markdown(
    """
This repository uses **separate Streamlit entrypoints** under `ui/`.\n
If you run `app.py` directly, it should *not* execute pipeline code (to avoid missing imports / undefined variables).\n
### Recommended way to test each feature

- **1) Upload a video**: run `ui/upload_ui.py`\n
- **2) Extract landmarks**: run `ui/landmarks_ui.py`\n
- **3) Run metrics + derived indicators + LLM feedback**: run `ui/processing_ui.py`\n
- **4) View dashboard**: run `ui/results_ui.py`\n
- **(Optional) Webcam sanity check**: run `ui/webcam_test.py`\n
- **(Optional) Audio + transcript generation**: run `ui/audio_ui.py`\n
### Commands (Windows PowerShell)
From the project root:\n
```bash
streamlit run ui/upload_ui.py
```\n
Then repeat with the other files above.\n
### OpenAI key (for LLM feedback)
Set your key before running **Generate Feedback**:\n
```bash
$env:OPENAI_API_KEY="YOUR_KEY_HERE"
```\n
"""
)

