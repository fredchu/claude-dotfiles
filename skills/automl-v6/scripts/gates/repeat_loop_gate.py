"""Repeat-loop detector — sliding window of 3 audit failures."""
import hashlib
from dataclasses import dataclass

WINDOW_SIZE = 3


@dataclass
class RepeatLoopGateResult:
    tripped: bool
    target_state: str | None = None
    reason: str = ""


def hash_audit_failure(failure: dict) -> str:
    """Stable hash of a single audit failure entry (criterion_id + reason)."""
    key = f"{failure.get('criterion_id', '')}|{failure.get('reason', '')}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def check_repeat_loop(state: dict) -> RepeatLoopGateResult:
    """Trip when the last WINDOW_SIZE audit failures all hash identically."""
    log = state.get("audit_failure_log", [])
    if len(log) < WINDOW_SIZE:
        return RepeatLoopGateResult(tripped=False)

    recent = log[-WINDOW_SIZE:]
    hashes = {hash_audit_failure(f) for f in recent}

    if len(hashes) == 1:
        return RepeatLoopGateResult(
            tripped=True,
            target_state="aborted",
            reason=f"repeat-loop: last {WINDOW_SIZE} audit failures identical",
        )
    return RepeatLoopGateResult(tripped=False)
