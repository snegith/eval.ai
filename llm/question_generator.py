import json
import os
import time
from typing import Dict, List, Literal, Optional

from google import genai
from pydantic import BaseModel, Field

from llm.feedback_engine import parse_json_response, validate_api_key


class QuestionGenerationError(Exception):
    """Raised when resume-based question generation fails."""


class GeneratedQuestion(BaseModel):
    category: Literal["technical", "project", "behavioral", "resume", "follow_up"]
    question: str
    rationale: str


class QuestionGenerationResponse(BaseModel):
    role_focus: str
    opening_prompt: str
    questions: List[GeneratedQuestion]


def _build_question_generation_prompt(profile: Dict[str, object]) -> str:
    profile_json = json.dumps(profile, indent=2)
    return f"""You are an expert technical interviewer.

Use the parsed resume profile below to generate personalized interview questions.

Your goals:
- Ask questions grounded in the candidate's actual background
- Cover technical depth, project ownership, and behavioral judgment
- Avoid generic filler questions when the resume gives enough signal
- Create questions that can meaningfully evaluate the candidate

=====================
PARSED RESUME PROFILE
=====================
{profile_json}

=====================
OUTPUT REQUIREMENTS
=====================

Return structured output with:
- role_focus: one short label for the likely interview focus
- opening_prompt: one short opening prompt for the interviewer
- questions: 8-10 personalized questions

Question mix:
- 2-3 technical questions
- 2-3 project questions
- 2 behavioral questions
- 1-2 resume-specific or follow-up questions

Each question must include:
- category
- question
- rationale

Important rules:
- Questions must reflect the technologies, projects, and experience in the resume.
- Rationale should explain what the interviewer is trying to learn.
- Keep questions concise but meaningful.
"""


def _validate_generated_questions(payload: Dict[str, object]) -> Dict[str, object]:
    role_focus = str(payload.get("role_focus") or "General Technical Interview").strip()
    opening_prompt = str(payload.get("opening_prompt") or "Walk me through the most relevant parts of your resume.").strip()
    raw_questions = payload.get("questions", [])

    questions: List[Dict[str, str]] = []
    if isinstance(raw_questions, list):
        for item in raw_questions:
            if not isinstance(item, dict):
                continue
            category = str(item.get("category") or "resume").strip().lower()
            if category not in {"technical", "project", "behavioral", "resume", "follow_up"}:
                category = "resume"
            question = str(item.get("question") or "").strip()
            rationale = str(item.get("rationale") or "").strip()
            if not question:
                continue
            questions.append({
                "category": category,
                "question": question,
                "rationale": rationale or "Used to explore the candidate's depth and ownership.",
            })

    if not questions:
        raise QuestionGenerationError("No usable questions were returned by the model.")

    return {
        "role_focus": role_focus,
        "opening_prompt": opening_prompt,
        "questions": questions[:10],
    }


def generate_questions_from_resume(
    profile: Dict[str, object],
    model: Optional[str] = None,
    max_retries: int = 3,
    timeout: int = 30,
    temperature: float = 0.4,
) -> Dict[str, object]:
    validate_api_key()

    if model is None:
        model = os.environ.get("GEMINI_QUESTION_MODEL", os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))

    prompt = _build_question_generation_prompt(profile)
    client = genai.Client()

    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": 2200,
                    "response_mime_type": "application/json",
                    "response_schema": QuestionGenerationResponse,
                },
            )

            parsed = getattr(response, "parsed", None)
            if isinstance(parsed, QuestionGenerationResponse):
                payload = parsed.model_dump()
            else:
                content = (response.text or "").strip()
                if not content:
                    raise QuestionGenerationError("Empty content in Gemini response")
                payload = parse_json_response(content)

            validated = _validate_generated_questions(payload)
            usage = getattr(response, "usage_metadata", None)
            validated["_metadata"] = {
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
            return validated
        except Exception as exc:
            last_error = exc
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue

    raise QuestionGenerationError(f"Failed after {max_retries} attempts. Last error: {last_error}")
