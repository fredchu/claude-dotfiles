"""Wall-time cap gate — ultimate safety against runaway long sessions."""
from dataclasses import dataclass
from datetime import datetime, timezone

DEFAULT_MAX_HOURS = 72


@dataclass
class WallTimeGateResult:
    tripped: bool
    target_state: str | None = None
    reason: str = ""


def check_wall_time_cap(state: dict, max_hours: int = DEFAULT_MAX_HOURS) -> WallTimeGateResult:
    """Trip when (now - active_session.started_at) >= max_hours."""
    active = state.get("active_session")
    if active is None:
        return WallTimeGateResult(tripped=False)

    started_at = datetime.fromisoformat(active["started_at"])
    now = datetime.now(timezone.utc).astimezone()
    elapsed_hours = (now - started_at).total_seconds() / 3600

    if elapsed_hours >= max_hours:
        return WallTimeGateResult(
            tripped=True,
            target_state="aborted",
            reason=f"wall-time cap reached: {elapsed_hours:.1f}h >= {max_hours}h",
        )
    return WallTimeGateResult(tripped=False)
