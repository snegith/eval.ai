import json
import os
import time
from typing import Dict, List, Literal, Optional

from google import genai
from pydantic import BaseModel, Field

from llm.feedback_engine import parse_json_response, validate_api_key


class ResumeReviewError(Exception):
    """Raised when Gemini-based resume review generation fails."""


class ResumeReviewResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    label: Literal["Strong", "Promising", "Needs Revision"]
    strengths: List[str]
    improvements: List[str]
    recommendations: List[str]
    summary: str


def _build_resume_review_prompt(resume_text: str, profile: Dict[str, object]) -> str:
    profile_json = json.dumps(profile, indent=2)
    preview = resume_text[:4500]

    return f"""You are an experienced technical recruiter and interview coach.

Your task is to review a candidate's resume and return a structured assessment.

You should evaluate:
- clarity of positioning
- strength of summary
- relevance and specificity of skills
- quality of experience bullets
- project quality and relevance
- evidence of impact, ownership, and measurable outcomes
- readiness for technical interview screening

Be honest, specific, and practical. Do not be generic.

=====================
PARSED RESUME PROFILE
=====================
{profile_json}

=====================
RAW RESUME TEXT
=====================
{preview}

=====================
OUTPUT REQUIREMENTS
=====================

Important rules:
- Strengths must be tied to evidence in the resume.
- Improvements should identify the highest-impact issues.
- Recommendations should be concrete and actionable.
- Keep each list concise and high signal.
"""


def _validate_resume_review(review: Dict[str, object]) -> Dict[str, object]:
    normalized = {
        "score": review.get("score", 0),
        "label": review.get("label", "Needs Revision"),
        "strengths": review.get("strengths", []),
        "improvements": review.get("improvements", []),
        "recommendations": review.get("recommendations", []),
        "summary": review.get("summary", "No summary provided."),
    }

    if not isinstance(normalized["score"], (int, float)):
        normalized["score"] = 0
    normalized["score"] = max(0, min(100, int(round(float(normalized["score"])))))

    if normalized["score"] >= 80:
        normalized["label"] = "Strong"
    elif normalized["score"] >= 65:
        normalized["label"] = "Promising"
    else:
        normalized["label"] = "Needs Revision"

    for key in ("strengths", "improvements", "recommendations"):
        if not isinstance(normalized[key], list):
            normalized[key] = []
        normalized[key] = [str(item).strip() for item in normalized[key] if str(item).strip()][:5]

    if not isinstance(normalized["summary"], str):
        normalized["summary"] = "No summary provided."

    return normalized


def generate_resume_review(
    resume_text: str,
    profile: Dict[str, object],
    model: Optional[str] = None,
    max_retries: int = 3,
    timeout: int = 30,
    temperature: float = 0.2,
) -> Dict[str, object]:
    validate_api_key()

    if model is None:
        model = os.environ.get("GEMINI_RESUME_MODEL", os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))

    prompt = _build_resume_review_prompt(resume_text, profile)
    client = genai.Client()

    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": 1800,
                    "response_mime_type": "application/json",
                    "response_schema": ResumeReviewResponse,
                },
            )

            parsed = getattr(response, "parsed", None)
            if isinstance(parsed, ResumeReviewResponse):
                review = _validate_resume_review(parsed.model_dump())
            else:
                content = (response.text or "").strip()
                if not content:
                    raise ResumeReviewError("Empty content in Gemini response")
                review = _validate_resume_review(parse_json_response(content))

            usage = getattr(response, "usage_metadata", None)
            review["_metadata"] = {
                "provider": "gemini",
                "model": model,
                "temperature": temperature,
                "input_tokens": getattr(usage, "prompt_token_count", 0) if usage else 0,
                "output_tokens": getattr(usage, "candidates_token_count", 0) if usage else 0,
                "total_tokens": getattr(usage, "total_token_count", 0) if usage else 0,
                "estimated_cost_usd": 0.0,
                "attempt": attempt + 1,
                "timeout": timeout,
            }
            return review
        except Exception as exc:
            last_error = exc
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue

    raise ResumeReviewError(f"Failed after {max_retries} attempts. Last error: {last_error}")
