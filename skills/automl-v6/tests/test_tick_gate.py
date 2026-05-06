from datetime import datetime, timedelta, timezone
import json
import pytest
from tick_gate import run_tick_gate


def _now_minus(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).astimezone().isoformat(timespec="seconds")


def _base_state(**overrides):
    state = {
        "lifecycle_state": "pursuing",
        "iterations": 5,
        "tokens": {"estimated": 100000, "actual": 20000, "by_round": []},
        "active_session": {
            "session_id": "s1", "pid": 1234,
            "started_at": _now_minus(1), "last_heartbeat": _now_minus(0),
        },
        "audit_failure_log": [],
        "criteria_progress": {"c1": {"status": "pursuing", "evidence": []}},
    }
    state.update(overrides)
    return state


@pytest.fixture
def quota_registry(tmp_path):
    d = tmp_path / "quota_registry"
    d.mkdir()
    (d / "claude_max.json").write_text(json.dumps({
        "quota_window": "", "total_used_pct": 0, "by_run": [], "last_updated": "",
    }))
    return d


def test_normal_state_returns_proceed():
    decision = run_tick_gate(_base_state(), audit_pass=True, blockers=[])
    assert decision.action == "next_round"


def test_iteration_cap_aborts():
    decision = run_tick_gate(_base_state(iterations=10000), audit_pass=True, blockers=[])
    assert decision.action == "transition"
    assert decision.target_state == "aborted"


def test_budget_cap_triggers_budget_limited():
    state = _base_state()
    state["tokens"]["actual"] = 80000
    decision = run_tick_gate(state, audit_pass=True, blockers=[])
    assert decision.action == "transition"
    assert decision.target_state == "budget-limited"
    assert decision.budget_limit_inject is True


def test_repeat_loop_aborts():
    state = _base_state()
    state["audit_failure_log"] = [
        {"criterion_id": "c1", "reason": "missing"},
        {"criterion_id": "c1", "reason": "missing"},
        {"criterion_id": "c1", "reason": "missing"},
    ]
    decision = run_tick_gate(state, audit_pass=True, blockers=[])
    assert decision.target_state == "aborted"


def test_terminal_state_short_circuits():
    """Already terminal → no further gate checks."""
    decision = run_tick_gate(_base_state(lifecycle_state="achieved"), audit_pass=True, blockers=[])
    assert decision.action == "noop"


def test_paused_state_short_circuits():
    decision = run_tick_gate(_base_state(lifecycle_state="paused"), audit_pass=True, blockers=[])
    assert decision.action == "noop"


def test_priority_order_quota_before_budget(quota_registry):
    """Quota gate (paused) takes precedence over budget gate (terminal)."""
    state = _base_state()
    state["tokens"]["actual"] = 80000  # would trip budget
    decision = run_tick_gate(
        state, audit_pass=True, blockers=[],
        own_quota_used_pct=80, quota_registry_dir=quota_registry,
        cli="claude_max", run_id="r1",
    )
    assert decision.action == "transition"
    assert decision.target_state == "paused"
