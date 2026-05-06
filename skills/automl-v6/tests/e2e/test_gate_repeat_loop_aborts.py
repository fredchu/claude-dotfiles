"""E2E: 3 identical audit failures → aborted."""
from datetime import datetime, timedelta, timezone
from orchestrator import decide_with_gates


def _now_minus(hours):
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).astimezone().isoformat(timespec="seconds")


def test_three_identical_audit_failures_abort():
    state = {
        "lifecycle_state": "pursuing",
        "iterations": 5,
        "tokens": {"estimated": 100000, "actual": 20000, "by_round": []},
        "active_session": {"session_id": "s1", "pid": 1, "started_at": _now_minus(1), "last_heartbeat": _now_minus(0)},
        "audit_failure_log": [
            {"criterion_id": "c1", "reason": "missing evidence"},
            {"criterion_id": "c1", "reason": "missing evidence"},
            {"criterion_id": "c1", "reason": "missing evidence"},
        ],
        "criteria_progress": {"c1": {"status": "pursuing", "evidence": []}},
    }

    decision = decide_with_gates(state, audit_pass=False, blockers=[])
    assert decision.action == "transition"
    assert decision.target_state == "aborted"


def test_three_distinct_audit_failures_no_abort():
    state = {
        "lifecycle_state": "pursuing",
        "iterations": 5,
        "tokens": {"estimated": 100000, "actual": 20000, "by_round": []},
        "active_session": {"session_id": "s1", "pid": 1, "started_at": _now_minus(1), "last_heartbeat": _now_minus(0)},
        "audit_failure_log": [
            {"criterion_id": "c1", "reason": "reason A"},
            {"criterion_id": "c1", "reason": "reason B"},
            {"criterion_id": "c1", "reason": "reason C"},
        ],
        "criteria_progress": {"c1": {"status": "pursuing", "evidence": []}},
    }

    decision = decide_with_gates(state, audit_pass=False, blockers=[])
    assert decision.action == "next_round"
