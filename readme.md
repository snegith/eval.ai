# 🎯 AI Interview Evaluation System

An end-to-end AI-powered mock interview evaluation pipeline that analyzes recorded interview videos using **computer vision**, **speech analysis**, and **LLM-generated feedback** to provide actionable, structured performance insights.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=black)
![MediaPipe](https://img.shields.io/badge/MediaPipe-CV-4285F4?logo=google&logoColor=white)
![Whisper](https://img.shields.io/badge/OpenAI_Whisper-ASR-412991?logo=openai&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)

---

## ✨ Features

| Module | What It Does |
|---|---|
| 🎥 **Video Analysis** | Extracts MediaPipe FaceMesh (478 pts) & Pose (33 pts) landmarks frame-by-frame |
| 👁️ **Eye Contact** | Measures gaze direction and sustained eye contact percentage |
| 🧍 **Posture Analysis** | Evaluates shoulder alignment, lean angle, and stability over time |
| 😊 **Facial Animation** | Tracks expressiveness via facial landmark movement variance |
| 🎤 **Audio Transcription** | Uses OpenAI Whisper for speech-to-text transcription |
| 🗣️ **Speech Metrics** | Analyzes speaking pace, filler words, and pause patterns |
| 🧠 **LLM Feedback** | Generates structured interview feedback using Google Gemini / OpenAI |
| 📄 **Resume Review** | AI-powered resume analysis and interview question generation |
| 📊 **Confidence Score** | Derives explainable confidence & nervousness indicators from metrics |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend (Vite)             │
│              Charts · Session Dashboard             │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────┐
│                 FastAPI Backend                      │
│   /sessions · /upload · /landmarks · /feedback      │
└──────┬──────────┬──────────┬──────────┬─────────────┘
       │          │          │          │
  ┌────▼───┐ ┌───▼────┐ ┌───▼───┐ ┌───▼────────┐
  │ Video  │ │ Audio  │ │ LLM   │ │ Analysis   │
  │Pipeline│ │Pipeline│ │Engine │ │ Pipeline   │
  └────────┘ └────────┘ └───────┘ └────────────┘
  MediaPipe   Whisper    Gemini/   Metrics &
  FaceMesh    ASR        OpenAI    Derived Scores
  + Pose
```

---

## 📁 Project Structure

```
AI_INT_EVAL/
├── api/                    # FastAPI backend (routes, schemas, services)
├── frontend/               # React + Vite + TailwindCSS dashboard
├── video/                  # CV pipeline (landmarks, eye contact, posture, animation)
├── audio/                  # Audio extraction, transcription, speech metrics
├── analysis/               # Session, audio, metrics, and feedback pipelines
├── llm/                    # LLM feedback engine, prompt templates, resume review
├── resume/                 # Resume parsing utilities
├── ui/                     # Streamlit UI pages (upload, processing, results)
├── utils/                  # Shared utility functions
├── data/sessions/          # Session artifacts (video, JSON results, feedback)
├── docker-compose.yml      # Docker orchestration
├── backend.Dockerfile      # Backend container
├── frontend.Dockerfile     # Frontend container (multi-stage with NGINX)
├── nginx.conf              # NGINX reverse proxy config
├── requirements.txt        # Python dependencies
└── readme.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- ffmpeg (for audio extraction)

### Local Development

**1. Backend (FastAPI):**
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

**2. Frontend (React):**
```powershell
cd frontend
npm install
npm run dev
```

### Docker Deployment

```bash
docker-compose up --build -d
```

This spins up:
- **Frontend** on port `80` (NGINX serving the React build)
- **Backend** on port `8000` (FastAPI with Uvicorn)

---

## 🔄 Pipeline Flow

1. **Upload** an interview video
2. **Extract** MediaPipe FaceMesh + Pose landmarks
3. **Analyze** behavioral signals:
   - Eye contact consistency
   - Posture stability & alignment
   - Facial expressiveness
4. **Transcribe** audio using Whisper
5. **Compute** speech metrics (pace, fillers, pauses)
6. **Derive** explainable indicators (confidence score, nervousness)
7. **Generate** structured LLM feedback from transcript + metrics
8. **Review** results on the dashboard

---

## 📦 Session Artifacts

Each interview run produces the following under `data/sessions/session_<id>/`:

| File | Description |
|---|---|
| `video.mp4` | Original uploaded video |
| `audio.wav` | Extracted audio track |
| `transcript.json` | Whisper transcription output |
| `audio_metrics.json` | Pace, fillers, and pause analysis |
| `landmarks.json` | Frame-by-frame face + pose landmarks |
| `eye_contact_results.json` | Gaze direction & eye contact scores |
| `posture_results.json` | Posture stability & alignment scores |
| `animation_results.json` | Facial expressiveness metrics |
| `derived_results.json` | Confidence & nervousness indicators |
| `feedback.json` | LLM-generated structured feedback |

---

## 📝 Notes

- Posture scoring fails closed when torso visibility is unreliable
- Emotion classification is not included as a production scoring stage
- Feedback generation halts if upstream metrics are invalid
- MediaPipe requires `protobuf<5` for compatibility

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn
- **Frontend**: React 18, Vite, TailwindCSS, Recharts, Framer Motion
- **Computer Vision**: MediaPipe FaceMesh & Pose, OpenCV
- **Speech**: OpenAI Whisper, MoviePy
- **LLM**: Google Gemini / OpenAI GPT
- **Deployment**: Docker, NGINX, Docker Compose

---

## 📄 License

This project is for educational and portfolio purposes.
