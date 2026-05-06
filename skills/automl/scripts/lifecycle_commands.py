"""User-facing lifecycle command mutators: pause / resume / clear.

Phase 5 of /automl v6. Each function takes a state dict and returns the
new state + a short status message. State mutation is in-place AND
returned; callers are expected to hand the returned state to atomic_update
or write_state.

`clear` is the only one that returns `None` for the state (caller deletes
the run dir on disk).
"""
from datetime import datetime, timezone

from lifecycle_fsm import transition

TERMINAL_LIFECYCLE_STATES = {"achieved", "unmet", "budget-limited", "aborted"}


class LifecycleCommandError(Exception):
    """Raised when a lifecycle command is not valid for the current state."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def pause(state: dict) -> tuple[dict, str]:
    """Transition pursuing -> paused; release active_session lock."""
    current = state.get("lifecycle_state")
    if current != "pursuing":
        raise LifecycleCommandError(f"not in pursuing (currently {current!r}); refuse pause")
    transition(current, "paused", reason="user pause")
    state["lifecycle_state"] = "paused"
    state["active_session"] = None
    state.setdefault("lifecycle_transitions", []).append({
        "from": "pursuing",
        "to": "paused",
        "ts": _now_iso(),
        "reason": "user pause",
    })
    return state, f"paused {state['run_id']}"


def resume(state: dict, session_id: str, pid: int) -> tuple[dict, str]:
    """Transition paused -> pursuing; claim active_session lock."""
    current = state.get("lifecycle_state")
    if current != "paused":
        raise LifecycleCommandError(f"not in paused (currently {current!r}); refuse resume")
    transition(current, "pursuing", reason="user resume")
    now = _now_iso()
    state["lifecycle_state"] = "pursuing"
    state["active_session"] = {
        "session_id": session_id,
        "pid": pid,
        "started_at": now,
        "last_heartbeat": now,
    }
    state.setdefault("lifecycle_transitions", []).append({
        "from": "paused",
        "to": "pursuing",
        "ts": now,
        "reason": "user resume",
    })
    return state, f"resumed {state['run_id']}"


def clear(state: dict) -> tuple[None, str]:
    """Refuse for non-terminal; return None state + cleared message for caller-side rmtree."""
    current = state.get("lifecycle_state")
    if current not in TERMINAL_LIFECYCLE_STATES:
        raise LifecycleCommandError(
            f"clear refused: lifecycle is {current!r}, must be terminal "
            f"(one of {sorted(TERMINAL_LIFECYCLE_STATES)})"
        )
    return None, f"cleared {state['run_id']}"
