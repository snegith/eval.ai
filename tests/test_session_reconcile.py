"""Tests for session metadata reconciliation and session listing."""

import json
from pathlib import Path

from storage.session_store import (
    create_session,
    list_sessions,
    reconcile_session_metadata,
    save_json,
    session_has_content,
    update_metadata,
)


def test_list_sessions_excludes_empty_initialized_sessions(isolated_data_dir):
    empty_id = create_session()
    populated_id = create_session()
    session_path = Path(isolated_data_dir) / populated_id
    (session_path / "landmarks.json").write_text(json.dumps({"fps": 30, "frames": []}), encoding="utf-8")

    listed = list_sessions()
    assert populated_id in listed
    assert empty_id not in listed
    assert session_has_content(populated_id) is True
    assert session_has_content(empty_id) is False


def test_reconcile_session_metadata_backfills_artifacts_and_status(isolated_data_dir):
    session_id = create_session()
    session_path = Path(isolated_data_dir) / session_id
    (session_path / "video.mp4").write_bytes(b"fake-video")
    (session_path / "eye_contact_results.json").write_text(
        json.dumps({"eye_contact_score": 72, "grade": "Good"}),
        encoding="utf-8",
    )
    (session_path / "animation_results.json").write_text(
        json.dumps({"expressiveness_score": 68, "grade": "Good"}),
        encoding="utf-8",
    )
    (session_path / "landmarks.json").write_text(json.dumps({"fps": 30, "frames": []}), encoding="utf-8")
    update_metadata(session_id, {"status": "initialized", "artifacts": {}})

    metadata = reconcile_session_metadata(session_id)
    assert metadata["status"] == "metrics_failed"
    assert metadata["artifacts"]["video"] is True
    assert metadata["artifacts"]["landmarks"] is True
    assert metadata["artifacts"]["eye_contact"] is True
    assert metadata["artifacts"]["animation"] is True


def test_reconcile_session_metadata_backfills_duration_from_transcript(isolated_data_dir):
    session_id = create_session()
    session_path = Path(isolated_data_dir) / session_id
    (session_path / "transcript.json").write_text(json.dumps({"duration_sec": 42.5}), encoding="utf-8")
    update_metadata(session_id, {"duration_seconds": 0.0})

    metadata = reconcile_session_metadata(session_id)
    assert metadata["duration_seconds"] == 42.5
