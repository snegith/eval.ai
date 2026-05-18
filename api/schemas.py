from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class AudioStageRequest(BaseModel):
    model_name: str = "base"
    pause_threshold: float = 2.0


class FullProcessRequest(BaseModel):
    run_audio: bool = True
    model_name: str = "base"
    pause_threshold: float = 2.0
    generate_feedback: bool = True
    parse_resume: bool = True
    generate_questions: bool = True


class SessionSummaryResponse(BaseModel):
    session_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    status: str = "unknown"
    duration_seconds: float = 0.0
    overall_score: Optional[float] = None
    has_feedback: bool = False
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    last_error: str = ""


class SessionBundleResponse(BaseModel):
    session_id: str
    metadata: Dict[str, Any]
    resume_text: Optional[Dict[str, Any]] = None
    resume_profile: Optional[Dict[str, Any]] = None
    resume_review: Optional[Dict[str, Any]] = None
    generated_questions: Optional[Dict[str, Any]] = None
    transcript: Optional[Dict[str, Any]] = None
    audio_metrics: Optional[Dict[str, Any]] = None
    landmarks: Optional[Dict[str, Any]] = None
    eye_contact: Optional[Dict[str, Any]] = None
    posture: Optional[Dict[str, Any]] = None
    animation: Optional[Dict[str, Any]] = None
    derived: Optional[Dict[str, Any]] = None
    feedback: Optional[Dict[str, Any]] = None


class StageResponse(BaseModel):
    status: str
    session_id: str
    data: Dict[str, Any] = Field(default_factory=dict)
