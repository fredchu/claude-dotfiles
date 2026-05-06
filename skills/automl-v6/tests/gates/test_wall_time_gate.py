from datetime import datetime, timedelta, timezone
from gates.wall_time_gate import check_wall_time_cap


def _now_minus(hours: int) -> str:
    t = datetime.now(timezone.utc) - timedelta(hours=hours)
    return t.astimezone().isoformat(timespec="seconds")


def test_under_cap_returns_pass():
    state = {"active_session": {"started_at": _now_minus(2)}}
    result = check_wall_time_cap(state, max_hours=72)
    assert result.tripped is False


def test_at_cap_returns_trip():
    state = {"active_session": {"started_at": _now_minus(73)}}
    result = check_wall_time_cap(state, max_hours=72)
    assert result.tripped is True
    assert result.target_state == "aborted"


def test_no_active_session_returns_pass():
    """If active_session is None (paused), wall-time check skipped."""
    state = {"active_session": None}
    result = check_wall_time_cap(state, max_hours=72)
    assert result.tripped is False


def test_default_max_is_72():
    state = {"active_session": {"started_at": _now_minus(71)}}
    result = check_wall_time_cap(state)
    assert result.tripped is False
