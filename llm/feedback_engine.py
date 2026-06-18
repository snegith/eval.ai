import concurrent.futures
import json
import os
import time
from typing import Any, Dict, Optional

from google import genai


class FeedbackGenerationError(Exception):
    """Custom exception for feedback generation failures."""


def validate_api_key() -> bool:
    """
    Validate that a Gemini API key is set.

    Gemini's official SDK automatically picks up either:
    - GEMINI_API_KEY
    - GOOGLE_API_KEY
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise FeedbackGenerationError(
            "Gemini API key not found. Set GEMINI_API_KEY or GOOGLE_API_KEY "
            "before calling generate_feedback()."
        )
    return True


def parse_json_response(content: str) -> Dict[str, Any]:
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

        for suffix in ('"}]}', '"]}', '"}', '"]', "}", "]"):
            try:
                return json.loads(content + suffix)
            except json.JSONDecodeError:
                continue

        raise FeedbackGenerationError(
            f"Failed to parse JSON response: {exc}\nRaw response: {content[:200]}..."
        ) from exc


def validate_feedback_structure(feedback: Dict[str, Any]) -> Dict[str, Any]:
    required_fields = {
        "overall_score": 0,
        "strengths": [],
        "improvements": [],
        "recommendations": [],
        "summary": "No summary provided",
    }
    optional_fields = {
        "score_breakdown": {
            "content": 0,
            "eye_contact": 0,
            "posture": 0,
            "animation": 0,
        },
        "star_analysis": {
            "applicable": False,
            "situation_score": None,
            "task_score": None,
            "action_score": None,
            "result_score": None,
            "overall_star_score": None,
            "feedback": "Not applicable",
        },
    }

    for field, default in required_fields.items():
        if field not in feedback:
            feedback[field] = default

    for field, default in optional_fields.items():
        if field not in feedback:
            feedback[field] = default

    if not isinstance(feedback["overall_score"], (int, float)):
        feedback["overall_score"] = 0
    if not isinstance(feedback["strengths"], list):
        feedback["strengths"] = []
    if not isinstance(feedback["improvements"], list):
        feedback["improvements"] = []
    if not isinstance(feedback["recommendations"], list):
        feedback["recommendations"] = []

    feedback["overall_score"] = max(0, min(100, feedback["overall_score"]))
    return feedback


def generate_feedback(
    transcript: str,
    metrics: dict,
    model: Optional[str] = None,
    max_retries: int = 3,
    timeout: int = 30,
    temperature: float = 0.2,
    debug: bool = False,
) -> Dict[str, Any]:
    validate_api_key()

    if model is None:
        model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    try:
        from llm.feedback_prompt import build_feedback_prompt, validate_metrics
    except ImportError as exc:
        raise FeedbackGenerationError(
            "Could not import feedback_prompt module. Ensure llm/feedback_prompt.py exists."
        ) from exc

    try:
        validated_metrics = validate_metrics(metrics)
    except ValueError as exc:
        raise FeedbackGenerationError(f"Invalid metrics: {exc}") from exc

    prompt = build_feedback_prompt(transcript, validated_metrics)

    if debug:
        print("=" * 60)
        print("DEBUG: Prompt being sent to Gemini")
        print("=" * 60)
        print(prompt[:500] + "...")
        print("=" * 60)

    client = genai.Client()

    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    client.models.generate_content,
                    model=model,
                    contents=prompt,
                    config={
                        "temperature": temperature,
                        "max_output_tokens": 2000,
                        "response_mime_type": "application/json",
                    },
                )
                try:
                    response = future.result(timeout=timeout)
                except concurrent.futures.TimeoutError as exc:
                    raise FeedbackGenerationError(
                        f"Gemini request timed out after {timeout} seconds"
                    ) from exc

            content = (response.text or "").strip()
            if not content:
                raise FeedbackGenerationError("Empty content in Gemini response")

            if debug:
                print("=" * 60)
                print("DEBUG: Raw response from Gemini")
                print("=" * 60)
                print(content)
                print("=" * 60)

            feedback = parse_json_response(content)
            feedback = validate_feedback_structure(feedback)

            usage = getattr(response, "usage_metadata", None)
            input_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
            output_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
            total_tokens = getattr(usage, "total_token_count", input_tokens + output_tokens) if usage else 0

            feedback["_metadata"] = {
                "provider": "gemini",
                "model": model,
                "temperature": temperature,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": 0.0,
                "attempt": attempt + 1,
                "timeout": timeout,
            }
            return feedback

        except Exception as exc:
            last_error = exc
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue

    raise FeedbackGenerationError(
        f"Failed after {max_retries} attempts. Last error: {last_error}"
    )


def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """
    Placeholder for Gemini pricing metadata.

    We keep the helper to avoid breaking imports, but return 0.0 until
    project-specific Gemini pricing rules are intentionally added.
    """
    _ = (input_tokens, output_tokens, model)
    return 0.0
