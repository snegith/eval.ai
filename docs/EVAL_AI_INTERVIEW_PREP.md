# EVAL.AI — Interview Prep Guide

> **Quick access:** One-page cheat sheet → [Section 1](#1-one-page-cheat-sheet) · STAR answers → [Section 2](#2-top-10-interview-questions--star-answers) · Key numbers → [Section 3](#3-key-numbers-to-memorize)

---

## 1. One-Page Cheat Sheet

### Elevator pitch (30 seconds)

> EVAL.AI is a full-stack mock interview evaluation platform I built with **FastAPI + React**. Users upload an interview video; the backend extracts **MediaPipe face and pose landmarks**, transcribes speech with **Whisper**, and computes explainable behavioral metrics — eye contact, posture, facial expressiveness. Those metrics plus the transcript feed **Gemini** to produce structured coaching feedback: scores, strengths, improvements, and recommendations. I also added **resume parsing** to generate personalized interview questions from PDFs.

---

### What it does (one line per module)

| Module | Input | Output | Tech |
|--------|-------|--------|------|
| **Landmarks** | Video frames | 478 face + 33 pose points per frame | OpenCV, MediaPipe |
| **Eye contact** | Landmarks | Gaze %, streak, stability | NumPy heuristics |
| **Posture** | Pose landmarks | Torso angle, shoulder tilt, grade | NumPy heuristics |
| **Animation** | Face landmarks | Expressiveness, consistency, stability | SciPy peak detection |
| **Audio** | Video | Transcript, WPM, fillers, pauses | Whisper, MoviePy |
| **Derived scores** | Above metrics | Confidence, nervousness | Weighted formulas |
| **Feedback** | Transcript + metrics | Structured coaching JSON | Gemini |
| **Resume** | PDF/TXT | Profile + questions | pypdf + Gemini |

---

### Pipeline flow (memorize this order)

```
Upload video
    → Extract landmarks (MediaPipe FaceMesh + Pose)
    → Transcribe audio (Whisper)
    → Compute metrics (eye contact, posture, animation)
    → Derive confidence & nervousness scores
    → Generate LLM feedback (only if all metrics valid)
    → Display on React dashboard
```

**Optional (separate flow):** Upload resume → parse → review → generate questions

---

### Architecture (3 sentences)

- **Frontend:** React + Vite dashboard — upload, sessions list, results with radar charts.
- **Backend:** FastAPI REST API orchestrates modular pipeline stages; each stage writes JSON artifacts to `data/sessions/session_<id>/`.
- **Deployment:** Docker Compose — NGINX serves React on port 80, proxies `/api/*` to FastAPI on 8000.

---

### Design decisions (say these confidently)

1. **Heuristics over deep learning for CV** — explainable, no training data, fast iteration.
2. **No emotion classification** — measures movement dynamics, not happy/sad labels.
3. **Fail-closed posture** — won't score when hip visibility is too low (head-only webcam).
4. **Feedback gated on valid metrics** — LLM blocked if upstream CV failed (no hallucinated scores).
5. **Artifact-based sessions** — every stage saves JSON; easy to debug and rerun individual stages.
6. **LLM fallbacks** — resume review and questions degrade gracefully on API failure.

---

### Tech stack (quick list)

`Python 3.11` · `FastAPI` · `React` · `Vite` · `TailwindCSS` · `OpenCV` · `MediaPipe` · `NumPy` · `SciPy` · `Whisper` · `Gemini` · `pypdf` · `Docker` · `NGINX`

---

### Known limitations (be honest)

- Head-only videos → posture fails (by design)
- Eye contact is 2D iris offset, not true 3D gaze
- Filler detection is regex, not phonetic
- Batch processing only (not real-time streaming)
- Gemini free tier can hit quota → fallback reviews

---

### API endpoints (if they ask)

| Endpoint | Purpose |
|----------|---------|
| `POST /api/sessions` | Create session |
| `POST /api/sessions/{id}/video` | Upload video |
| `POST /api/sessions/{id}/resume` | Upload resume |
| `POST /api/sessions/{id}/resume/parse` | Parse resume |
| `POST /api/sessions/{id}/questions/generate` | Generate questions |
| `POST /api/sessions/{id}/process` | Run full pipeline |
| `GET /api/sessions/{id}/results` | Get all artifacts |

---

## 2. Top 10 Interview Questions — STAR Answers

---

### Q1. Walk me through your project end to end.

**Situation:** Candidates practicing for interviews often don't get objective feedback on both *what* they say and *how* they present themselves — eye contact, posture, pacing, filler words.

**Task:** Build an end-to-end platform that analyzes a recorded mock interview and returns actionable, structured coaching.

**Action:**
- Designed a modular pipeline: video upload → MediaPipe landmark extraction → behavioral metric computation → Whisper transcription → Gemini feedback generation.
- Built a FastAPI backend with separate stage endpoints so each step is independently testable and rerunnable.
- Created a React dashboard showing radar charts, score gauges, and expandable feedback sections.
- Extended it with resume parsing (pypdf + section heuristics) and LLM-generated personalized interview questions.

**Result:** A working platform that produces 10+ JSON artifacts per session (landmarks, eye contact, posture, animation, transcript, audio metrics, derived scores, feedback). Users get explainable scores plus AI coaching grounded in real computed metrics, not hallucinated numbers.

---

### Q2. How does your eye contact detection work?

**Situation:** Eye contact is a key interview signal, but raw MediaPipe output is noisy frame-to-frame.

**Task:** Build a reliable, explainable eye contact percentage from facial landmarks.

**Action:**
- Used MediaPipe FaceMesh **refined iris landmarks** (indices 474–477, 469–472) to find iris centers.
- Computed normalized gaze offset: iris position relative to inter-eye face center, divided by eye width.
- Applied a **5-frame moving average** to reduce jitter.
- Classified each frame as "looking" if horizontal offset < 0.025 and vertical offset < 0.035.
- Tracked secondary signals: longest sustained streak, gaze stability (std dev).

**Result:** Per-session eye contact percentage, grade (Excellent/Good/Fair/Poor), and streak metrics — all derived from geometry, fully inspectable in JSON output.

---

### Q3. Why heuristics instead of a trained ML model for CV metrics?

**Situation:** I needed behavioral metrics (eye contact, posture, expressiveness) without a labeled dataset of interview videos.

**Task:** Choose an approach that is explainable, fast to build, and debuggable.

**Action:**
- Used MediaPipe for landmark detection (pre-trained, production-ready).
- Built geometric heuristics on top: gaze offset ratios for eye contact, torso angle for posture, landmark movement variance for expressiveness.
- Documented every threshold in `config.py` so they can be tuned.
- Explicitly avoided emotion classification (would need labeled data, hard to explain, culturally biased).

**Result:** Metrics I can explain line-by-line in an interview. Tradeoff: sensitive to camera framing and lighting, which I handle with fail-closed logic and user-facing tips.

---

### Q4. Tell me about a hard technical problem you solved.

**Situation:** MediaPipe landmark extraction was failing in some environments — wrong landmark counts, cryptic protobuf errors.

**Task:** Make the CV pipeline reliable across development setups.

**Action:**
- Discovered MediaPipe 0.10.14 requires **protobuf < 5** on Python 3.11; newer protobuf silently breaks landmark output.
- Pinned dependencies in `requirements.txt` and added runtime validation in `landmarks.py`.
- Built `validate_landmarks.py` to sanity-check face/pose coverage before running downstream metrics.
- Added video rotation detection (0°, 90°, 180°) because phone-recorded videos often have wrong orientation.

**Result:** Integration tests pass consistently; invalid landmark files fail early with clear error messages instead of producing garbage scores downstream.

---

### Q5. How does LLM feedback stay grounded and not hallucinate?

**Situation:** LLMs can invent plausible-sounding scores that don't match the actual video analysis.

**Task:** Ensure feedback is tied to real computed data.

**Action:**
- LLM receives only the **Whisper transcript** + **pre-computed numeric metrics** (eye contact %, posture %, expressiveness, confidence, nervousness) — never raw video.
- Feedback generation is **blocked entirely** if any metric stage returned an error.
- Prompt includes explicit scores and grades so the model reasons from facts.
- Response parsed as structured JSON with schema validation, 3 retries, and markdown-stripping fallback.
- Temperature set to 0.2 for consistency.

**Result:** Feedback JSON always references real pipeline outputs. When metrics fail (e.g., posture unavailable), the system skips feedback rather than fabricating scores.

---

### Q6. How does posture analysis work, and what happens when it fails?

**Situation:** Posture scoring needs shoulder and hip landmarks, but many users record head-only webcam videos.

**Task:** Score posture when possible; refuse to score when data is unreliable.

**Action:**
- Used MediaPipe Pose landmarks: shoulders (11, 12), hips (23, 24).
- Computed torso angle and shoulder tilt per frame; counted "good posture" frames.
- Required hip visibility above 0.2 threshold for reliable scoring.
- If >40% of frames use ear-based fallback (no visible hips), **fail closed** with an actionable tip: "Keep shoulders and upper torso in frame."
- Persisted error stubs in JSON so the UI shows a clear message instead of a misleading score.

**Result:** Honest scoring — users with proper framing get posture metrics; head-only videos get a helpful tip instead of a fake 85% posture score.

---

### Q7. Why did you choose this architecture (FastAPI + artifact-based sessions)?

**Situation:** The pipeline has 6+ sequential stages, each potentially slow (Whisper, MediaPipe) and failure-prone.

**Task:** Design for debuggability, partial reruns, and clean separation of concerns.

**Action:**
- Each stage writes JSON artifacts to `data/sessions/session_<id>/` (landmarks.json, eye_contact_results.json, etc.).
- FastAPI exposes individual stage endpoints (`/landmarks`, `/audio`, `/metrics`, `/feedback`) plus a combined `/process`.
- Session metadata tracks status and which artifacts exist.
- Frontend fetches the full bundle via `GET /results` and normalizes it for charts.

**Result:** I can rerun just the metrics stage after tweaking thresholds without re-running Whisper. Debugging is as simple as opening a JSON file. The modular design also maps cleanly to future async job queues.

---

### Q8. Tell me about the resume parsing extension.

**Situation:** Mock interview prep isn't complete without tailored questions based on the candidate's background.

**Task:** Parse resumes and generate personalized interview questions.

**Action:**
- Built a rule-based parser: pypdf for PDF text extraction, regex for emails/phones/links, section header matching for skills/experience/projects/education.
- Structured output saved as `resume_profile.json`.
- Gemini generates 8–10 categorized questions (technical, project, behavioral, resume-specific) from the parsed profile.
- Added rule-based fallbacks for both resume review and question generation when Gemini is unavailable or hits quota.

**Result:** Users upload a PDF, get structured profile data plus tailored questions in under a minute. The flow is optional and separate from video evaluation so each can be tested independently.

---

### Q9. How would you scale this for production?

**Situation:** Current design runs synchronously — a 5-minute video blocks the API request for several minutes.

**Task:** Explain a credible scaling path without over-engineering what I built.

**Action (what I'd do next):**
- Move processing to **async job queue** (Celery + Redis): upload returns immediately, poll for status.
- Store artifacts in **S3/cloud storage** instead of local filesystem.
- Cache Whisper model in memory across requests (already partially done with global model singleton).
- Add **horizontal scaling** for CV workers separate from API servers.
- Rate-limit Gemini calls; batch resume reviews.

**Result:** Current artifact-based design already supports this — each stage is a discrete job reading/writing JSON. Migration path is clear without rewriting the pipeline logic.

---

### Q10. What would you do differently if you rebuilt it today?

**Situation:** After building and testing the full pipeline, several limitations became clear.

**Task:** Show self-awareness and growth mindset.

**Action (retrospective):**
- Add **async processing** from day one instead of synchronous API calls.
- Use **proper gaze estimation** (e.g., head pose + iris combined) instead of pure 2D offset.
- Build a **small labeled dataset** (50–100 clips) to validate eye contact thresholds empirically.
- Integrate resume flow into the main pipeline toggle instead of a separate UI path.
- Add **unit tests** for each metric function with synthetic landmark data.
- Consider **on-device processing** (MediaPipe runs in browser via WebAssembly) for privacy.

**Result:** The current system is a strong MVP that proves the concept. These improvements would move it toward production quality — and I'm ready to discuss tradeoffs for each.

---

## 3. Key Numbers to Memorize

| Parameter | Value | Meaning |
|-----------|-------|---------|
| FaceMesh landmarks | ~478 per frame | Includes refined iris points |
| Pose landmarks | 33 per frame | Shoulders, hips, etc. |
| Eye gaze threshold X | 0.025 | Normalized horizontal offset |
| Eye gaze threshold Y | 0.035 | Normalized vertical offset |
| Smoothing window | 5 frames | Moving average for gaze |
| Torso angle threshold | 15° | Max lean for "good posture" |
| Hip visibility threshold | 0.2 | Min confidence to use hip landmarks |
| Max fallback ratio | 0.4 (40%) | Posture fails if too many fallback frames |
| Animation window | 30 frames | ~1 sec at 30fps |
| Confidence formula | `(eye×0.6 + posture×0.4) × 0.9` | Capped at 95 |
| Nervousness formula | `100 - (consistency×0.6 + stability×0.4)` | Higher = more jitter |
| Whisper model | `base` | Speed/accuracy tradeoff |
| Gemini model | `gemini-2.5-flash` | Default for feedback |
| LLM temperature | 0.2 | Low for consistent output |
| LLM max retries | 3 | With JSON parse fallback |

---

## 4. Quick-Fire Answers (1–2 sentences each)

**Q: Is this emotion detection?**
> No. I measure facial *movement dynamics* — expressiveness, consistency, stability — not emotion labels like happy or nervous. Derived "nervousness" is a mathematical composite of movement variability, not an emotion classifier.

**Q: Can someone game the system?**
> Partially — staring at the camera boosts eye contact but the LLM still evaluates transcript quality. The system evaluates delivery and content together, not just one signal.

**Q: Why Gemini over OpenAI?**
> Free tier availability, good structured JSON output, and the `google-genai` SDK supports schema-constrained generation. The code also accepts `GOOGLE_API_KEY` as an alias.

**Q: What's in the feedback JSON?**
> `overall_score`, `score_breakdown` (content, eye contact, posture, animation), `strengths`, `improvements`, `recommendations`, `summary`, and optional `star_analysis`.

**Q: How do you handle privacy?**
> Currently local file storage. For production I'd add encryption at rest, retention policies, and explicit consent before processing biometric data.

**Q: What's the difference from HireVue?**
> HireVue is enterprise-grade with proprietary models and human review workflows. EVAL.AI is an explainable, modular MVP focused on transparent heuristics and open artifact inspection — better for learning and iteration.

---

## 5. Questions to Ask the Interviewer

1. "Does your team work on multimodal ML pipelines combining CV and NLP?"
2. "How do you validate heuristic models vs. learned models in production?"
3. "What's your approach to LLM output reliability — structured generation, RAG, or human review?"
4. "How do you handle long-running ML inference in your API architecture?"

---

## 6. Before the Interview — 5-Minute Checklist

- [ ] Can you draw the pipeline flow on a whiteboard?
- [ ] Can you explain eye contact math in 30 seconds?
- [ ] Can you explain why posture fails closed?
- [ ] Can you name 3 design decisions and their tradeoffs?
- [ ] Can you name 2 limitations honestly?
- [ ] Do you know the confidence and nervousness formulas?
- [ ] Can you explain how LLM feedback is grounded?

---

*Generated for EVAL.AI project interview preparation. Review alongside the codebase in `api/`, `video/`, `analysis/`, `llm/`, and `resume/`.*
