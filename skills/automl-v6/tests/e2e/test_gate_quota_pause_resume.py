"""E2E: quota gate trips → paused, then resumes after quota window passes."""
import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta, timezone
from orchestrator import decide_with_gates


def _now_minus(hours):
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).astimezone().isoformat(timespec="seconds")


@pytest.fixture
def quota_registry(tmp_path):
    d = tmp_path / "quota_registry"
    d.mkdir()
    (d / "claude_max.json").write_text(json.dumps({
        "quota_window": "2026-05-06T14:00 → 19:00",
        "total_used_pct": 0,
        "by_run": [],
        "last_updated": _now_minus(0),
    }))
    return d


def _state():
    return {
        "lifecycle_state": "pursuing",
        "iterations": 5,
        "tokens": {"estimated": 100000, "actual": 20000, "by_round": []},
        "active_session": {"session_id": "s1", "pid": 1, "started_at": _now_minus(1), "last_heartbeat": _now_minus(0)},
        "audit_failure_log": [],
        "criteria_progress": {"c1": {"status": "pursuing", "evidence": []}},
    }


def test_quota_high_pauses_then_low_resumes(quota_registry: Path):
    state = _state()

    high = decide_with_gates(
        state, audit_pass=True, blockers=[],
        own_quota_used_pct=80, quota_registry_dir=quota_registry,
        cli="claude_max", run_id="r1",
    )
    assert high.action == "transition"
    assert high.target_state == "paused"

    state["lifecycle_state"] = "pursuing"
    low = decide_with_gates(
        state, audit_pass=True, blockers=[],
        own_quota_used_pct=10, quota_registry_dir=quota_registry,
        cli="claude_max", run_id="r1",
    )
    assert low.action == "next_round"
