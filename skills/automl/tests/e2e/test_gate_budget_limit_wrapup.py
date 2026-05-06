"""E2E: budget gate trips → budget-limited + injection signal."""
from datetime import datetime, timedelta, timezone
from orchestrator import decide_with_gates
from tick_gate import run_tick_gate


def _now_minus(hours):
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).astimezone().isoformat(timespec="seconds")


def test_budget_at_80_percent_wraps_up():
    state = {
        "lifecycle_state": "pursuing",
        "iterations": 5,
        "tokens": {"estimated": 100000, "actual": 80000, "by_round": []},
        "active_session": {"session_id": "s1", "pid": 1, "started_at": _now_minus(1), "last_heartbeat": _now_minus(0)},
        "audit_failure_log": [],
        "criteria_progress": {"c1": {"status": "pursuing", "evidence": []}},
    }

    decision = decide_with_gates(state, audit_pass=True, blockers=[])
    assert decision.action == "transition"
    assert decision.target_state == "budget-limited"

    raw = run_tick_gate(state, audit_pass=True, blockers=[])
    assert raw.budget_limit_inject is True


def test_no_budget_strategy_does_not_trip():
    state = {
        "lifecycle_state": "pursuing",
        "iterations": 5,
        "tokens": {"estimated": 100000, "actual": 200000, "by_round": []},
        "budget_strategy": "none",
        "active_session": {"session_id": "s1", "pid": 1, "started_at": _now_minus(1), "last_heartbeat": _now_minus(0)},
        "audit_failure_log": [],
        "criteria_progress": {"c1": {"status": "pursuing", "evidence": []}},
    }

    decision = decide_with_gates(state, audit_pass=True, blockers=[])
    assert decision.action == "next_round"
