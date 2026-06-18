"""Tests for resilient JSON parsing and resume review recovery."""

import json

from api.services import _safe_load_artifact
from llm.feedback_engine import parse_json_response


def test_parse_json_response_repairs_truncated_object():
    truncated = """{
  "score": 65,
  "label": "Promising",
  "strengths": [
    "Strong academic foundation"
  ],
  "improvements": [
    "Add more measurable outcomes"
  ],
  "recommendations": [
    "Rewrite project bullets with impact metrics"
  ],
  "summary": "Promising profile with room to tighten impact language"""

    parsed = parse_json_response(truncated)
    assert parsed["score"] == 65
    assert parsed["label"] == "Promising"
    assert parsed["strengths"][0].startswith("Strong academic")


def test_safe_load_artifact_recovers_failed_resume_review(isolated_data_dir):
    from storage.session_store import create_session, save_json

    session_id = create_session()
    save_json(session_id, "resume_text.json", {"full_text": "Built APIs with Python and React."})
    save_json(
        session_id,
        "resume_profile.json",
        {
            "summary": "Software engineer focused on backend systems.",
            "skills": ["Python", "React", "FastAPI"],
            "experience": [{"title": "Engineer", "company": "Acme"}],
            "projects": [{"name": "Interview Platform"}],
        },
    )
    save_json(session_id, "resume_review.json", {"error": "Failed to parse JSON response"})

    review = _safe_load_artifact(session_id, "resume_review")
    assert review is not None
    assert review.get("error") is None
    assert review.get("score", 0) > 0
    assert review.get("_metadata", {}).get("recovered_from_stored_error") is True
