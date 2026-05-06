"""E2E: a second /automl from the same cwd refuses unless overridden."""
import json
from datetime import datetime, timedelta, timezone

import pytest

from orchestrator import start_or_resume_run


def _fresh_iso(minutes_ago: float = 1) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).astimezone().isoformat(timespec="seconds")


def _seed_active_run(automl_dir, run_id):
    d = automl_dir / run_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "state.json").write_text(json.dumps({
        "lifecycle_state": "pursuing",
        "active_session": {
            "session_id": "first",
            "pid": 1111,
            "started_at": _fresh_iso(30),
            "last_heartbeat": _fresh_iso(1),
        },
        "goal_summary": "Refactor auth",
    }))


def test_second_session_refused_with_actionable_message(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    _seed_active_run(automl, run_id="20260506-160000-aaaa")

    with pytest.raises(SystemExit) as exc_info:
        start_or_resume_run(
            cwd=tmp_path,
            automl_dir=automl,
            session_id="second",
            pid=2222,
            allow_cwd_conflict=False,
            autonomous=True,
        )

    msg = str(exc_info.value)
    assert "20260506-160000-aaaa" in msg
    assert "git worktree add" in msg
    assert "--allow-cwd-conflict" in msg


def test_override_flag_bypasses_refusal(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    _seed_active_run(automl, run_id="20260506-160000-bbbb")

    result = start_or_resume_run(
        cwd=tmp_path,
        automl_dir=automl,
        session_id="second",
        pid=2222,
        allow_cwd_conflict=True,
        autonomous=True,
    )
    assert result.cwd_decision.refuse is False
    assert result.cwd_decision.warning is True
