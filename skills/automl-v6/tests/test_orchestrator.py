from datetime import datetime, timedelta, timezone
from orchestrator import decide_next_action, apply_round_output_to_state, decide_with_gates


def _now_minus(hours):
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).astimezone().isoformat(timespec="seconds")


def test_decide_all_achieved_returns_terminal_achieved():
    state = {
        "lifecycle_state": "pursuing",
        "criteria_progress": {
            "c1": {"status": "achieved", "evidence": [{"type": "file_change", "path": "x", "summary": "y"}]},
            "c2": {"status": "achieved", "evidence": [{"type": "file_change", "path": "x", "summary": "y"}]},
        },
    }
    decision = decide_next_action(state, audit_pass=True, blockers=[])
    assert decision.action == "transition"
    assert decision.target_state == "achieved"


def test_decide_audit_fail_keeps_pursuing():
    state = {
        "lifecycle_state": "pursuing",
        "criteria_progress": {
            "c1": {"status": "achieved", "evidence": []},
        },
    }
    decision = decide_next_action(state, audit_pass=False, blockers=[])
    assert decision.action == "next_round"


def test_decide_blockers_with_no_progress_returns_unmet():
    state = {
        "lifecycle_state": "pursuing",
        "criteria_progress": {
            "c1": {"status": "blocked", "evidence": []},
        },
    }
    decision = decide_next_action(
        state, audit_pass=True, blockers=["external API down"], rounds_without_progress=3
    )
    assert decision.action == "transition"
    assert decision.target_state == "unmet"


def test_decide_pursuing_with_progress_continues():
    state = {
        "lifecycle_state": "pursuing",
        "criteria_progress": {
            "c1": {"status": "pursuing", "evidence": []},
            "c2": {"status": "achieved", "evidence": [{"type": "file_change", "path": "x", "summary": "y"}]},
        },
    }
    decision = decide_next_action(state, audit_pass=True, blockers=[])
    assert decision.action == "next_round"


def test_apply_round_output_updates_criteria_progress():
    state = {
        "criteria_progress": {
            "c1": {"status": "pending", "evidence": []},
            "c2": {"status": "pending", "evidence": []},
        },
        "iterations": 0,
        "tokens": {"actual": 0, "by_round": []},
    }
    round_output = {
        "round_id": 1,
        "tokens_used_this_round": 8400,
        "criteria_progress_update": {
            "c1": {"status": "pursuing", "evidence": []},
        },
        "blockers": [],
    }
    new_state = apply_round_output_to_state(state, round_output)
    assert new_state["criteria_progress"]["c1"]["status"] == "pursuing"
    assert new_state["criteria_progress"]["c2"]["status"] == "pending"
    assert new_state["iterations"] == 1
    assert new_state["tokens"]["actual"] == 8400
    assert new_state["tokens"]["by_round"] == [{"round": 1, "tokens": 8400}]


def test_apply_round_output_reverts_audit_failed_achieved_to_pursuing():
    state = {
        "criteria_progress": {"c1": {"status": "pending", "evidence": []}},
        "iterations": 0,
        "tokens": {"actual": 0, "by_round": []},
        "audit_failure_log": [],
    }
    round_output = {
        "round_id": 1,
        "tokens_used_this_round": 1000,
        "criteria_progress_update": {
            "c1": {"status": "achieved", "evidence": []},
        },
        "blockers": [],
    }
    new_state = apply_round_output_to_state(
        state, round_output,
        audit_failures=[("c1", "missing required evidence types: ['audit_check', 'command_output', 'file_change']")],
    )
    assert new_state["criteria_progress"]["c1"]["status"] == "pursuing"
    assert len(new_state["audit_failure_log"]) == 1
    assert new_state["audit_failure_log"][0]["criterion_id"] == "c1"


def test_decide_with_gates_budget_trip_overrides_normal_decision():
    state = {
        "lifecycle_state": "pursuing",
        "iterations": 5,
        "tokens": {"estimated": 100000, "actual": 85000, "by_round": []},
        "active_session": {"session_id": "s", "pid": 1, "started_at": _now_minus(1), "last_heartbeat": _now_minus(0)},
        "audit_failure_log": [],
        "criteria_progress": {"c1": {"status": "pursuing", "evidence": []}},
    }
    decision = decide_with_gates(state, audit_pass=True, blockers=[])
    assert decision.action == "transition"
    assert decision.target_state == "budget-limited"


def test_decide_with_gates_no_trip_falls_to_normal_decision():
    state = {
        "lifecycle_state": "pursuing",
        "iterations": 5,
        "tokens": {"estimated": 100000, "actual": 20000, "by_round": []},
        "active_session": {"session_id": "s", "pid": 1, "started_at": _now_minus(1), "last_heartbeat": _now_minus(0)},
        "audit_failure_log": [],
        "criteria_progress": {
            "c1": {"status": "achieved", "evidence": [{"type": "file_change", "path": "x", "summary": "y"}]},
        },
    }
    decision = decide_with_gates(state, audit_pass=True, blockers=[])
    assert decision.action == "transition"
    assert decision.target_state == "achieved"
