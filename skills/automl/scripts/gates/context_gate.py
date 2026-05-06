"""Context usage gate — advisory at 60/65/70/75%, hard transition at 80%."""
from dataclasses import dataclass

ALERT_BUCKETS = [60, 65, 70, 75]
HARD_THRESHOLD = 0.80


@dataclass
class ContextGateResult:
    tripped: bool
    target_state: str | None = None
    pause_reason: str | None = None
    reason: str = ""
    alert_bucket: int | None = None


def classify_context_alert(used_pct: float) -> int | None:
    """Return the highest bucket reached (60/65/70/75/80) or None if below 60%."""
    pct_int = int(used_pct * 100)
    if pct_int >= 80:
        return 80
    for bucket in reversed(ALERT_BUCKETS):
        if pct_int >= bucket:
            return bucket
    return None


def check_context_usage(used_pct: float) -> ContextGateResult:
    """Trip (paused / context_critical) at 80%; advisory at 60-75%."""
    if used_pct >= HARD_THRESHOLD:
        return ContextGateResult(
            tripped=True,
            target_state="paused",
            pause_reason="context_critical",
            reason=f"context usage {used_pct:.0%} >= {HARD_THRESHOLD:.0%}",
            alert_bucket=80,
        )
    bucket = classify_context_alert(used_pct)
    return ContextGateResult(tripped=False, alert_bucket=bucket)
