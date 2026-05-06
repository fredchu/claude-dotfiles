"""FIXED ORDER tick gate orchestrator.

Order (must not be reordered without spec approval):
1. paused short-circuit (already paused → noop)
2. terminal short-circuit (achieved/unmet/budget-limited/aborted → noop)
3. quota gate (claude_max + codex)
4. context gate
5. budget gate (calibrated)
6. repeat-loop detector
7. iteration cap
8. wall-time cap
9. else → next_round (orchestrator.decide_next_action handles achievement logic)
"""
from dataclasses import dataclass
from pathlib import Path

from gates.budget_gate import check_budget_cap
from gates.iteration_gate import check_iteration_cap
from gates.wall_time_gate import check_wall_time_cap
from gates.repeat_loop_gate import check_repeat_loop
from gates.context_gate import check_context_usage
from gates.quota_gate import check_quota

TERMINAL_STATES = {"achieved", "unmet", "budget-limited", "aborted"}


@dataclass
class TickGateDecision:
    action: str  # "noop" | "next_round" | "transition"
    target_state: str | None = None
    pause_reason: str | None = None
    reason: str = ""
    budget_limit_inject: bool = False
    alert_bucket: int | None = None


def run_tick_gate(
    state: dict,
    audit_pass: bool,
    blockers: list[str],
    own_quota_used_pct: float = 0,
    context_used_pct: float = 0,
    quota_registry_dir: Path | None = None,
    cli: str = "claude_max",
    run_id: str = "",
) -> TickGateDecision:
    """Run all gates in FIXED ORDER. Return first tripped gate's decision."""
    if state.get("lifecycle_state") == "paused":
        return TickGateDecision(action="noop", reason="already paused")

    if state.get("lifecycle_state") in TERMINAL_STATES:
        return TickGateDecision(action="noop", reason="already terminal")

    if quota_registry_dir is not None:
        q = check_quota(quota_registry_dir, cli, run_id, own_quota_used_pct)
        if q.tripped:
            return TickGateDecision(
                action="transition", target_state=q.target_state,
                pause_reason=q.pause_reason, reason=q.reason,
            )

    c = check_context_usage(context_used_pct)
    if c.tripped:
        return TickGateDecision(
            action="transition", target_state=c.target_state,
            pause_reason=c.pause_reason, reason=c.reason,
            alert_bucket=c.alert_bucket,
        )

    b = check_budget_cap(state)
    if b.tripped:
        return TickGateDecision(
            action="transition", target_state=b.target_state,
            reason=b.reason, budget_limit_inject=b.injection_required,
        )

    r = check_repeat_loop(state)
    if r.tripped:
        return TickGateDecision(
            action="transition", target_state=r.target_state, reason=r.reason,
        )

    i = check_iteration_cap(state)
    if i.tripped:
        return TickGateDecision(
            action="transition", target_state=i.target_state, reason=i.reason,
        )

    w = check_wall_time_cap(state)
    if w.tripped:
        return TickGateDecision(
            action="transition", target_state=w.target_state, reason=w.reason,
        )

    return TickGateDecision(
        action="next_round",
        reason="no gates tripped; orchestrator will decide achievement",
        alert_bucket=c.alert_bucket,
    )
