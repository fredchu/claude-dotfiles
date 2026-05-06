"""E2E: in autonomous mode, orphans (paused + heartbeat>1h) are silently
reclaimed and lifecycle moved back to pursuing without prompting the user."""
import json
from datetime import datetime, timedelta, timezone

from orchestrator import start_or_resume_run


def _hb_minus(hours: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).astimezone().isoformat(timespec="seconds")


def _seed(automl, run_id, hb_hours_ago, lifecycle="paused"):
    d = automl / run_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "state.json").write_text(json.dumps({
        "lifecycle_state": lifecycle,
        "lifecycle_transitions": [],
        "active_session": {
            "session_id": "ghost",
            "pid": 1,
            "started_at": _hb_minus(hb_hours_ago + 1),
            "last_heartbeat": _hb_minus(hb_hours_ago),
        },
    }))


def test_only_stale_paused_runs_are_taken_over(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    _seed(automl, run_id="orphan-1", hb_hours_ago=2.5, lifecycle="paused")
    _seed(automl, run_id="fresh-paused", hb_hours_ago=0.2, lifecycle="paused")
    _seed(automl, run_id="achieved-old", hb_hours_ago=10, lifecycle="achieved")

    # fresh-paused (paused but alive) counts as a concurrent peer for cwd
    # advisory; in an autonomous context the operator opts in via the override
    # flag, mirroring how launchd-style scheduled runs would invoke /automl.
    result = start_or_resume_run(
        cwd=tmp_path,
        automl_dir=automl,
        session_id="autopilot",
        pid=7777,
        autonomous=True,
        allow_cwd_conflict=True,
    )

    assert result.takeover.silent is True
    assert set(result.taken_over_run_ids) == {"orphan-1"}

    fresh = json.loads((automl / "fresh-paused" / "state.json").read_text())
    assert fresh["active_session"]["session_id"] == "ghost", "fresh paused untouched"

    achieved = json.loads((automl / "achieved-old" / "state.json").read_text())
    assert achieved["lifecycle_state"] == "achieved", "terminal runs untouched"

    orphan = json.loads((automl / "orphan-1" / "state.json").read_text())
    assert orphan["lifecycle_state"] == "pursuing"
    assert orphan["active_session"]["session_id"] == "autopilot"


def test_no_orphans_no_takeover(tmp_path):
    automl = tmp_path / ".automl"
    automl.mkdir()
    result = start_or_resume_run(
        cwd=tmp_path,
        automl_dir=automl,
        session_id="autopilot",
        pid=7777,
        autonomous=True,
    )
    assert result.takeover.silent is False
    assert result.taken_over_run_ids == []
