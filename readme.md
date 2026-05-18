AI Interview Evaluation

This project evaluates a mock interview session from recorded video using:

- Computer vision for behavioral signals
- Audio transcription and speech metrics
- LLM-generated structured feedback
- A session-based Streamlit workflow
- A FastAPI backend for frontend integration

Session Layout

Each interview run is stored under:

```text
data/sessions/session_xxxxxxxx/
```

Common artifacts:

```text
video.mp4
audio.wav
transcript.json
audio_metrics.json
landmarks.json
eye_contact_results.json
posture_results.json
animation_results.json
derived_results.json
feedback.json
metadata.json
```

Current Pipeline

1. Upload interview video
2. Extract MediaPipe FaceMesh and Pose landmarks
3. Run behavioral analysis:
   - Eye contact
   - Posture
   - Facial animation
4. Derive explainable indicators:
   - Confidence score
   - Nervousness indicator
5. Generate LLM feedback from transcript + metrics
6. Review results in Streamlit

FastAPI Integration

The backend API now wraps the same session pipeline and exposes endpoints for:

- creating sessions
- uploading video
- running audio/transcript
- extracting landmarks
- running metrics
- generating feedback
- retrieving session results

Run the API from the project root:

```powershell
.venv\Scripts\activate
uvicorn api.main:app --reload
```

Notes

- Emotion classification is not currently implemented as a production scoring stage.
- Posture scoring now fails closed when torso visibility is not reliable enough.
- Feedback generation now stops if upstream metrics are invalid.

Recommended Streamlit Entrypoints

```powershell
streamlit run ui/upload_ui.py
streamlit run ui/landmarks_ui.py
streamlit run ui/audio_ui.py
streamlit run ui/processing_ui.py
streamlit run ui/results_ui.py
```

Environment

Use the project virtual environment. The MediaPipe pipeline expects Python 3.11 and `protobuf<5`.

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```
