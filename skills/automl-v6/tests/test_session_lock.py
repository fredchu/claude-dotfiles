from datetime import datetime, timedelta, timezone

from session_lock import (
    HEARTBEAT_STALE_ORPHAN,
    HEARTBEAT_STALE_RESUME,
    can_takeover,
    is_session_alive,
    update_heartbeat,
)


def _now_minus_minutes(m: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=m)).astimezone().isoformat(timespec="seconds")


def test_update_heartbeat_writes_now():
    state = {
        "active_session": {
            "session_id": "s1",
            "pid": 1,
            "started_at": _now_minus_minutes(60),
            "last_heartbeat": _now_minus_minutes(5),
        }
    }
    update_heartbeat(state)
    hb = datetime.fromisoformat(state["active_session"]["last_heartbeat"])
    delta = (datetime.now(timezone.utc).astimezone() - hb).total_seconds()
    assert delta < 5


def test_update_heartbeat_noop_when_no_active_session():
    state = {"active_session": None}
    update_heartbeat(state)
    assert state["active_session"] is None


def test_is_session_alive_recent():
    state = {
        "active_session": {
            "session_id": "s1",
            "pid": 1,
            "started_at": _now_minus_minutes(10),
            "last_heartbeat": _now_minus_minutes(2),
        }
    }
    assert is_session_alive(state) is True


def test_is_session_alive_stale():
    state = {
        "active_session": {
            "session_id": "s1",
            "pid": 1,
            "started_at": _now_minus_minutes(60),
            "last_heartbeat": _now_minus_minutes(15),
        }
    }
    assert is_session_alive(state) is False


def test_can_takeover_resume_threshold():
    """Heartbeat > 10min -> can take over (resume conflict scenario)."""
    state = {
        "active_session": {
            "session_id": "s1",
            "pid": 1,
            "started_at": _now_minus_minutes(60),
            "last_heartbeat": _now_minus_minutes(11),
        }
    }
    assert can_takeover(state, threshold=HEARTBEAT_STALE_RESUME) is True


def test_can_takeover_orphan_threshold_blocks_recent():
    """1h threshold blocks 30min stale (still within 1h)."""
    state = {
        "active_session": {
            "session_id": "s1",
            "pid": 1,
            "started_at": _now_minus_minutes(60),
            "last_heartbeat": _now_minus_minutes(30),
        }
    }
    assert can_takeover(state, threshold=HEARTBEAT_STALE_ORPHAN) is False


def test_no_active_session_takeover_safe():
    """active_session=None means session voluntarily released - always safe to claim."""
    state = {"active_session": None}
    assert can_takeover(state, threshold=HEARTBEAT_STALE_RESUME) is True
