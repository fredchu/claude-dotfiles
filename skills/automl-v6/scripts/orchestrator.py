"""Main session decision logic between rounds.

Reads state.json after each round subagent returns + audit verdict, decides:
- transition to terminal lifecycle (achieved / unmet / aborted)
- next round
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from tick_gate import run_tick_gate


@dataclass
class OrchestratorDecision:
    action: str  # "next_round" | "transition" | "halt"
    target_state: str | None = None
    reason: str = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def decide_next_action(
    state: dict,
    audit_pass: bool,
    blockers: list[str],
    rounds_without_progress: int = 0,
    blocked_threshold: int = 3,
) -> OrchestratorDecision:
    """Decide next action after a round completes.

    Decision order (Phase 1 subset; Phase 2 adds budget / quota / repeat-loop):
    1. All criteria achieved + audit pass → transition to "achieved"
    2. Blockers + N rounds no progress → transition to "unmet"
    3. Audit fail OR pursuing criteria remain → next_round
    """
    progress = state.get("criteria_progress", {})

    if not progress:
        return OrchestratorDecision(action="halt", reason="no criteria defined")

    statuses = [c["status"] for c in progress.values()]
    all_achieved = all(s == "achieved" for s in statuses)
    any_blocked = any(s == "blocked" for s in statuses)

    if all_achieved and audit_pass:
        return OrchestratorDecision(
            action="transition", target_state="achieved",
            reason="all criteria achieved + audit pass",
        )

    if any_blocked and blockers and rounds_without_progress >= blocked_threshold:
        return OrchestratorDecision(
            action="transition", target_state="unmet",
            reason=f"blocked + {rounds_without_progress} rounds no progress",
        )

    return OrchestratorDecision(
        action="next_round",
        reason=f"audit_pass={audit_pass}, blockers={len(blockers)}, statuses={statuses}",
    )


def apply_round_output_to_state(
    state: dict,
    round_output: dict,
    audit_failures: list[tuple[str, str]] | None = None,
) -> dict:
    """Apply round subagent output + audit results to state dict."""
    audit_failures = audit_failures or []
    failed_ids = {cid for cid, _ in audit_failures}

    for cid, criterion_update in round_output["criteria_progress_update"].items():
        new_status = criterion_update["status"]
        if cid in failed_ids and new_status == "achieved":
            new_status = "pursuing"
        state["criteria_progress"][cid] = {
            "status": new_status,
            "evidence": criterion_update.get("evidence", []),
        }
        if "next_step_attempt" in criterion_update:
            state["criteria_progress"][cid]["next_step_attempt"] = criterion_update["next_step_attempt"]

    state["tokens"]["actual"] += round_output["tokens_used_this_round"]
    state["tokens"]["by_round"].append({
        "round": round_output["round_id"],
        "tokens": round_output["tokens_used_this_round"],
    })

    state["iterations"] = state.get("iterations", 0) + 1

    if audit_failures:
        state.setdefault("audit_failure_log", [])
        for cid, reason in audit_failures:
            state["audit_failure_log"].append({
                "round_id": round_output["round_id"],
                "criterion_id": cid,
                "reason": reason,
                "ts": _now_iso(),
            })

    return state


def decide_with_gates(
    state: dict,
    audit_pass: bool,
    blockers: list[str],
    own_quota_used_pct: float = 0,
    context_used_pct: float = 0,
    quota_registry_dir: Path | None = None,
    cli: str = "claude_max",
    run_id: str = "",
    rounds_without_progress: int = 0,
) -> OrchestratorDecision:
    """Combine tick_gate (gates) + decide_next_action (achievement logic).

    Tick gate has priority — if any gate trips, use that decision.
    Otherwise fall through to Phase 1's decide_next_action.
    """
    gate_decision = run_tick_gate(
        state, audit_pass, blockers,
        own_quota_used_pct=own_quota_used_pct,
        context_used_pct=context_used_pct,
        quota_registry_dir=quota_registry_dir,
        cli=cli, run_id=run_id,
    )

    if gate_decision.action in ("noop", "transition"):
        return OrchestratorDecision(
            action=gate_decision.action,
            target_state=gate_decision.target_state,
            reason=gate_decision.reason,
        )

    return decide_next_action(state, audit_pass, blockers, rounds_without_progress)
