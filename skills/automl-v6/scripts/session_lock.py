"""Active session lock + heartbeat policy.

Phase 3: cross-session multi-run safety.

Heartbeat thresholds:
- HEARTBEAT_STALE_RESUME (10 min) -- resume conflict scenario; another session
  may take over if heartbeat older than this.
- HEARTBEAT_STALE_ORPHAN (1 hour) -- orphan recovery scan threshold.
"""
from datetime import datetime, timedelta, timezone

HEARTBEAT_STALE_RESUME = timedelta(minutes=10)
HEARTBEAT_STALE_ORPHAN = timedelta(hours=1)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def update_heartbeat(state: dict) -> None:
    """Stamp now into active_session.last_heartbeat (in-place mutation).

    No-op if active_session is None (voluntarily released).
    """
    if state.get("active_session"):
        state["active_session"]["last_heartbeat"] = _now_iso()


def is_session_alive(state: dict, threshold: timedelta = HEARTBEAT_STALE_RESUME) -> bool:
    """True iff active_session exists and heartbeat is more recent than threshold."""
    active = state.get("active_session")
    if active is None:
        return False
    hb = datetime.fromisoformat(active["last_heartbeat"])
    elapsed = datetime.now(timezone.utc).astimezone() - hb
    return elapsed < threshold


def can_takeover(state: dict, threshold: timedelta) -> bool:
    """True iff no active session OR heartbeat older than threshold.

    Threshold determines policy:
    - HEARTBEAT_STALE_RESUME (10 min) for foreground resume conflicts
    - HEARTBEAT_STALE_ORPHAN (1 hour) for orphan recovery scan
    """
    if state.get("active_session") is None:
        return True
    return not is_session_alive(state, threshold)
