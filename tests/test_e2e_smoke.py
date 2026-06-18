"""End-to-end API smoke test: session lifecycle through full processing."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from tests.conftest import default_test_video_path, mediapipe_runtime_ready

TEST_VIDEO = default_test_video_path()
HAS_GEMINI_KEY = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "ok"


def test_session_crud_and_list(client, isolated_data_dir):
    create_resp = client.post("/api/sessions")
    assert create_resp.status_code == 200
    session_id = create_resp.json()["session_id"]
    assert session_id

    get_resp = client.get(f"/api/sessions/{session_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["session_id"] == session_id

    list_resp = client.get("/api/sessions")
    assert list_resp.status_code == 200
    ids = [item["session_id"] for item in list_resp.json()]
    assert session_id not in ids

    session_path = isolated_data_dir / session_id
    (session_path / "landmarks.json").write_text('{"fps": 30, "total_frames": 1, "frames": []}', encoding="utf-8")
    list_resp = client.get("/api/sessions")
    ids = [item["session_id"] for item in list_resp.json()]
    assert session_id in ids


@pytest.mark.skipif(
    not mediapipe_runtime_ready(),
    reason="MediaPipe requires protobuf<5 in a Python 3.11 virtual environment",
)
@pytest.mark.skipif(
    not os.path.exists(TEST_VIDEO),
    reason=f"Test video not found at {TEST_VIDEO}",
)
def test_full_pipeline_smoke(client, isolated_data_dir):
    """Upload video and run the full processing pipeline."""
    create_resp = client.post("/api/sessions")
    assert create_resp.status_code == 200
    session_id = create_resp.json()["session_id"]

    with open(TEST_VIDEO, "rb") as video_file:
        upload_resp = client.post(
            f"/api/sessions/{session_id}/video",
            files={"file": ("smoke_test.mp4", video_file, "video/mp4")},
        )
    assert upload_resp.status_code == 200, upload_resp.text
    assert upload_resp.json()["status"] == "ok"

    process_resp = client.post(
        f"/api/sessions/{session_id}/process",
        json={
            "run_audio": True,
            "model_name": "base",
            "pause_threshold": 2.0,
            "generate_feedback": HAS_GEMINI_KEY,
            "parse_resume": False,
            "generate_questions": False,
        },
    )
    assert process_resp.status_code == 200, process_resp.text
    payload = process_resp.json()
    assert payload["status"] in {"ok", "partial", "error"}, payload
    data = payload["data"]

    landmarks = data.get("landmarks") or {}
    assert not landmarks.get("error"), f"Landmarks failed: {landmarks.get('error')}"

    metrics = data.get("metrics") or {}
    assert metrics, "Metrics stage returned no payload"
    metric_results = metrics.get("metrics") or metrics
    assert metric_results.get("eye_contact"), "Missing eye contact metrics"
    assert metric_results.get("animation"), "Missing animation metrics"
    # Posture may fail closed when hip visibility is low (expected for some test videos).

    results_resp = client.get(f"/api/sessions/{session_id}/results")
    assert results_resp.status_code == 200
    bundle = results_resp.json()
    assert bundle["landmarks"] is not None
    assert bundle["eye_contact"] is not None
    assert bundle["animation"] is not None

    session_path = isolated_data_dir / session_id
    assert session_path.is_dir(), f"Session artifacts directory missing: {session_path}"
    assert (session_path / "landmarks.json").exists()
    assert (session_path / "eye_contact_results.json").exists()
