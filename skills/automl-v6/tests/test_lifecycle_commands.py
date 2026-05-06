from datetime import datetime, timezone

import pytest

from lifecycle_commands import (
    LifecycleCommandError,
    pause,
    resume,
    clear,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _pursuing_state():
    return {
        "schema_version": "v6.0",
        "run_id": "20260506-200000-pause",
        "lifecycle_state": "pursuing",
        "lifecycle_transitions": [{"from": None, "to": "aligning", "ts": _now_iso(), "reason": "init"}],
        "active_session": {"session_id": "s1", "pid": 1, "started_at": _now_iso(), "last_heartbeat": _now_iso()},
        "criteria_progress": {"c1": {"status": "pursuing", "evidence": []}},
        "tokens": {"estimated": 50000, "actual": 10000, "by_round": []},
        "iterations": 1,
        "expected_wake_at": None,
        "audit_failure_log": [],
    }


def _paused_state():
    s = _pursuing_state()
    s["lifecycle_state"] = "paused"
    s["active_session"] = None
    return s


def _terminal_state(lifecycle="achieved"):
    s = _pursuing_state()
    s["lifecycle_state"] = lifecycle
    s["active_session"] = None
    return s


def test_pause_pursuing_transitions_to_paused():
    state = _pursuing_state()
    new_state, msg = pause(state)
    assert new_state["lifecycle_state"] == "paused"
    assert new_state["active_session"] is None
    assert "paused" in msg.lower()


def test_pause_records_transition():
    state = _pursuing_state()
    new_state, _ = pause(state)
    last = new_state["lifecycle_transitions"][-1]
    assert last["from"] == "pursuing"
    assert last["to"] == "paused"
    assert "user pause" in last["reason"].lower()


def test_pause_already_paused_raises():
    state = _paused_state()
    with pytest.raises(LifecycleCommandError, match="not in pursuing"):
        pause(state)


def test_pause_terminal_raises():
    state = _terminal_state("achieved")
    with pytest.raises(LifecycleCommandError):
        pause(state)


def test_resume_paused_transitions_to_pursuing():
    state = _paused_state()
    new_state, msg = resume(state, session_id="s2", pid=99)
    assert new_state["lifecycle_state"] == "pursuing"
    assert new_state["active_session"]["session_id"] == "s2"
    assert new_state["active_session"]["pid"] == 99
    assert "resumed" in msg.lower()


def test_resume_pursuing_raises():
    state = _pursuing_state()
    with pytest.raises(LifecycleCommandError, match="not in paused"):
        resume(state, session_id="s2", pid=99)


def test_resume_records_transition():
    state = _paused_state()
    new_state, _ = resume(state, session_id="s2", pid=99)
    last = new_state["lifecycle_transitions"][-1]
    assert last["from"] == "paused"
    assert last["to"] == "pursuing"
    assert "user resume" in last["reason"].lower()


def test_clear_terminal_returns_none_state():
    state = _terminal_state("achieved")
    result, msg = clear(state)
    assert result is None
    assert "cleared" in msg.lower()


def test_clear_pursuing_raises():
    state = _pursuing_state()
    with pytest.raises(LifecycleCommandError, match="terminal"):
        clear(state)


def test_clear_paused_raises():
    state = _paused_state()
    with pytest.raises(LifecycleCommandError):
        clear(state)
