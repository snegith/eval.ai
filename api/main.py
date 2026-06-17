from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    AudioStageRequest,
    FullProcessRequest,
    HealthResponse,
    SessionBundleResponse,
    SessionSummaryResponse,
    StageResponse,
)
from api.services import (
    build_session_bundle,
    build_session_summary,
    create_empty_session,
    generate_questions_for_session,
    parse_resume_for_session,
    run_audio_only,
    run_feedback_only,
    run_full_processing_for_session,
    run_landmarks_for_session,
    run_metrics_only,
    save_uploaded_resume,
    save_uploaded_video,
)
from storage.session_store import list_sessions, session_exists


app = FastAPI(
    title="AI Interview Evaluation API",
    version="1.0.0",
    description="FastAPI wrapper around the interview evaluation pipeline.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _not_found_if_missing(session_id: str) -> None:
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")


def _stage_status_from_summary(summary: dict | None) -> str:
    status = str((summary or {}).get("status", "ok"))
    if "failed" in status or status == "error":
        return "error"
    return "ok"


def _has_usable_metrics(result: dict) -> bool:
    metrics = result.get("metrics") or {}
    metric_results = metrics.get("metrics") if isinstance(metrics.get("metrics"), dict) else metrics
    if not isinstance(metric_results, dict):
        return False

    for key in ("eye_contact", "posture", "animation"):
        payload = metric_results.get(key) or {}
        if isinstance(payload, dict) and not payload.get("error"):
            return True
    return False


def _process_stage_status(result: dict | None) -> str:
    """Return ok, partial, or error for full-session processing."""
    result = result or {}
    landmarks = result.get("landmarks") or {}
    if isinstance(landmarks, dict) and landmarks.get("error"):
        return "error"

    summary = result.get("summary") or {}
    summary_status = str(summary.get("status", "ok"))
    summary_failed = "failed" in summary_status or summary_status == "error"

    if _has_usable_metrics(result):
        return "partial" if summary_failed else "ok"

    return "error" if summary_failed else "ok"


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse()


@app.get("/api/sessions", response_model=List[SessionSummaryResponse])
def get_sessions() -> List[SessionSummaryResponse]:
    return [SessionSummaryResponse(**build_session_summary(session_id)) for session_id in reversed(list_sessions())]


@app.post("/api/sessions", response_model=SessionSummaryResponse)
def create_session_endpoint() -> SessionSummaryResponse:
    return SessionSummaryResponse(**create_empty_session())


@app.get("/api/sessions/{session_id}", response_model=SessionSummaryResponse)
def get_session(session_id: str) -> SessionSummaryResponse:
    _not_found_if_missing(session_id)
    return SessionSummaryResponse(**build_session_summary(session_id))


@app.get("/api/sessions/{session_id}/results", response_model=SessionBundleResponse)
def get_session_results(session_id: str) -> SessionBundleResponse:
    _not_found_if_missing(session_id)
    return SessionBundleResponse(**build_session_bundle(session_id))


@app.post("/api/sessions/{session_id}/video", response_model=StageResponse)
async def upload_video(session_id: str, file: UploadFile = File(...)) -> StageResponse:
    _not_found_if_missing(session_id)
    suffix = Path(file.filename or "video.mp4").suffix or ".mp4"
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        result = save_uploaded_video(session_id, temp_path, file.filename or f"video{suffix}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        Path(temp_path).unlink(missing_ok=True)

    return StageResponse(status="ok", session_id=session_id, data=result)


@app.post("/api/sessions/{session_id}/resume", response_model=StageResponse)
async def upload_resume(session_id: str, file: UploadFile = File(...)) -> StageResponse:
    _not_found_if_missing(session_id)
    suffix = Path(file.filename or "resume.pdf").suffix or ".pdf"
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        result = save_uploaded_resume(session_id, temp_path, file.filename or f"resume{suffix}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        Path(temp_path).unlink(missing_ok=True)

    return StageResponse(status="ok", session_id=session_id, data=result)


@app.post("/api/sessions/{session_id}/resume/parse", response_model=StageResponse)
def parse_resume_stage(session_id: str) -> StageResponse:
    _not_found_if_missing(session_id)
    try:
        result = parse_resume_for_session(session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    status = "error" if isinstance(result, dict) and result.get("error") else "ok"
    return StageResponse(status=status, session_id=session_id, data=result)


@app.post("/api/sessions/{session_id}/questions/generate", response_model=StageResponse)
def generate_questions_stage(session_id: str) -> StageResponse:
    _not_found_if_missing(session_id)
    try:
        result = generate_questions_for_session(session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    status = "error" if isinstance(result, dict) and result.get("error") else "ok"
    return StageResponse(status=status, session_id=session_id, data=result)


@app.post("/api/sessions/{session_id}/audio", response_model=StageResponse)
def run_audio_stage(session_id: str, request: AudioStageRequest) -> StageResponse:
    _not_found_if_missing(session_id)
    try:
        result = run_audio_only(
            session_id,
            model_name=request.model_name,
            pause_threshold=request.pause_threshold,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    status = "error" if isinstance(result, dict) and result.get("error") else "ok"
    return StageResponse(status=status, session_id=session_id, data=result)


@app.post("/api/sessions/{session_id}/landmarks", response_model=StageResponse)
def run_landmarks_stage(session_id: str) -> StageResponse:
    _not_found_if_missing(session_id)
    try:
        result = run_landmarks_for_session(session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    status = "error" if isinstance(result, dict) and result.get("error") else "ok"
    return StageResponse(status=status, session_id=session_id, data=result)


@app.post("/api/sessions/{session_id}/metrics", response_model=StageResponse)
def run_metrics_stage_endpoint(session_id: str) -> StageResponse:
    _not_found_if_missing(session_id)
    try:
        result = run_metrics_only(session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return StageResponse(status=result.get("status", "ok"), session_id=session_id, data=result)


@app.post("/api/sessions/{session_id}/feedback", response_model=StageResponse)
def run_feedback_stage_endpoint(session_id: str) -> StageResponse:
    _not_found_if_missing(session_id)
    try:
        result = run_feedback_only(session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return StageResponse(status=result.get("status", "ok"), session_id=session_id, data=result)


@app.post("/api/sessions/{session_id}/process", response_model=StageResponse)
def run_full_process(session_id: str, request: FullProcessRequest) -> StageResponse:
    _not_found_if_missing(session_id)
    try:
        result = run_full_processing_for_session(
            session_id,
            run_audio=request.run_audio,
            model_name=request.model_name,
            pause_threshold=request.pause_threshold,
            generate_feedback=request.generate_feedback,
            parse_resume=request.parse_resume,
            generate_questions=request.generate_questions,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return StageResponse(status=_process_stage_status(result), session_id=session_id, data=result)


@app.post("/api/sessions/process-upload", response_model=StageResponse)
async def process_upload(
    file: UploadFile = File(...),
    resume: UploadFile | None = File(None),
    run_audio: bool = Form(True),
    model_name: str = Form("base"),
    pause_threshold: float = Form(2.0),
    generate_feedback: bool = Form(True),
    parse_resume: bool = Form(True),
    generate_questions: bool = Form(True),
) -> StageResponse:
    session_summary = create_empty_session()
    session_id = session_summary["session_id"]
    suffix = Path(file.filename or "video.mp4").suffix or ".mp4"

    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        save_uploaded_video(session_id, temp_path, file.filename or f"video{suffix}")
        if resume is not None:
            resume_suffix = Path(resume.filename or "resume.pdf").suffix or ".pdf"
            with NamedTemporaryFile(delete=False, suffix=resume_suffix) as resume_temp_file:
                resume_content = await resume.read()
                resume_temp_file.write(resume_content)
                resume_temp_path = resume_temp_file.name
            try:
                save_uploaded_resume(session_id, resume_temp_path, resume.filename or f"resume{resume_suffix}")
            finally:
                Path(resume_temp_path).unlink(missing_ok=True)
        result = run_full_processing_for_session(
            session_id,
            run_audio=run_audio,
            model_name=model_name,
            pause_threshold=pause_threshold,
            generate_feedback=generate_feedback,
            parse_resume=parse_resume,
            generate_questions=generate_questions,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        Path(temp_path).unlink(missing_ok=True)

    return StageResponse(status=_process_stage_status(result), session_id=session_id, data=result)
