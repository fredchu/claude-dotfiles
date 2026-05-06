"""E2E: a stale paused run is taken over by an autonomous follow-up session.

Mirrors the Phase 5 pause/resume call path that orchestrator.start_or_resume_run
will eventually feed; for Phase 3 the takeover_orphan helper materialises the
state mutation directly.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from orchestrator import start_or_resume_run


def _hb_minus(hours: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).astimezone().isoformat(timespec="seconds")


def _seed_paused_run(automl: Path, run_id: str, hb_hours_ago: float):
    d = automl / run_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "state.json").write_text(json.dumps({
        "lifecycle_state": "paused",
        "lifecycle_transitions": [
            {"from": "pursuing", "to": "paused", "ts": _hb_minus(hb_hours_ago + 0.5),
             "reason": "previous session crashed"},
        ],
        "active_session": {
            "session_id": "old-session",
            "pid": 9999,
            "started_at": _hb_minus(hb_hours_ago + 1),
            "last_heartbeat": _hb_minus(hb_hours_ago),
        },
    }))


def test_autonomous_session_takes_over_stale_paused_run(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    _seed_paused_run(automl, run_id="stale-1", hb_hours_ago=2.0)

    result = start_or_resume_run(
        cwd=tmp_path,
        automl_dir=automl,
        session_id="new-session",
        pid=12345,
        autonomous=True,
    )

    assert result.cwd_decision.refuse is False
    assert result.takeover.silent is True
    assert "stale-1" in result.taken_over_run_ids

    data = json.loads((automl / "stale-1" / "state.json").read_text())
    assert data["active_session"]["session_id"] == "new-session"
    assert data["active_session"]["pid"] == 12345
    assert data["lifecycle_state"] == "pursuing"
    assert data["lifecycle_transitions"][-1]["to"] == "pursuing"
    assert "orphan takeover" in data["lifecycle_transitions"][-1]["reason"]


def test_interactive_session_does_not_silently_take_over(tmp_path):
    """Interactive mode surfaces orphans for the user, doesn't auto-claim them."""
    automl = tmp_path / ".automl"
    automl.mkdir()
    _seed_paused_run(automl, run_id="stale-1", hb_hours_ago=2.0)

    result = start_or_resume_run(
        cwd=tmp_path,
        automl_dir=automl,
        session_id="new-session",
        pid=12345,
        autonomous=False,
    )

    assert result.takeover.prompt_user is True
    assert result.taken_over_run_ids == []

    data = json.loads((automl / "stale-1" / "state.json").read_text())
    assert data["active_session"]["session_id"] == "old-session"
    assert data["lifecycle_state"] == "paused"
