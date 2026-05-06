"""Main session decision logic between rounds.

Reads state.json after each round subagent returns + audit verdict, decides:
- transition to terminal lifecycle (achieved / unmet / aborted)
- next round
"""
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from orphan_recovery import (
    TakeoverDecision,
    classify_takeover_action,
    scan_for_orphans,
)
from round_dispatch import record_round_boundary
from run_summary import write_run_summary
from session_lock import update_heartbeat
from tick_gate import run_tick_gate
from worktree_advisory import CwdConflictDecision, check_cwd_conflict


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

    record_round_boundary(state)

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


@dataclass
class StartupResult:
    """Result of `start_or_resume_run` -- threaded through the CLI entrypoint.

    Phase 3: feeds the actual takeover wiring (Phase 5 surfaces pause/resume).
    """
    cwd_decision: CwdConflictDecision
    takeover: TakeoverDecision
    taken_over_run_ids: list = field(default_factory=list)


def takeover_orphan(
    automl_dir: Path, run_id: str, session_id: str, pid: int,
) -> dict:
    """Claim a stale paused run: rewrite active_session, move to pursuing.

    The previous session is presumed dead (heartbeat older than 1h). We do not
    require fcntl here because `can_takeover` already gated on heartbeat
    staleness; concurrent takeover attempts would race but converge on
    whichever writes last (acceptable for orphan recovery).
    """
    state_path = automl_dir / run_id / "state.json"
    data = json.loads(state_path.read_text())

    now = _now_iso()
    data["active_session"] = {
        "session_id": session_id,
        "pid": pid,
        "started_at": now,
        "last_heartbeat": now,
    }
    if data.get("lifecycle_state") == "paused":
        prev = data["lifecycle_state"]
        data["lifecycle_state"] = "pursuing"
        data.setdefault("lifecycle_transitions", []).append({
            "from": prev,
            "to": "pursuing",
            "ts": now,
            "reason": f"orphan takeover by session {session_id}",
        })
    state_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return data


def start_or_resume_run(
    cwd: Path,
    automl_dir: Path,
    session_id: str,
    pid: int,
    allow_cwd_conflict: bool = False,
    autonomous: bool = False,
) -> StartupResult:
    """Phase 3 startup gate sequence.

    1. Worktree advisory -- refuse same-cwd concurrent runs unless override.
    2. Orphan scan -- find paused runs with >1h stale heartbeat.
    3. Classify takeover plan based on autonomous vs interactive.
    4. In autonomous mode, silently take over orphans now.

    The actual round-loop entry happens after this returns; the CLI
    entrypoint wires init_state / resume_state in Phase 1+2 paths.
    """
    cwd_decision = check_cwd_conflict(
        cwd=cwd, automl_dir=automl_dir, allow_override=allow_cwd_conflict,
    )
    if cwd_decision.refuse:
        raise SystemExit(cwd_decision.message)

    orphans = scan_for_orphans(automl_dir=automl_dir)
    mode = "autonomous" if autonomous else "interactive"
    takeover_plan = classify_takeover_action(mode=mode, orphans=orphans)

    taken: list[str] = []
    if takeover_plan.silent:
        for orphan in takeover_plan.orphans:
            takeover_orphan(automl_dir, orphan["run_id"], session_id, pid)
            taken.append(orphan["run_id"])

    return StartupResult(
        cwd_decision=cwd_decision,
        takeover=takeover_plan,
        taken_over_run_ids=taken,
    )


def heartbeat_state_path(state_path: Path) -> None:
    """Read state.json, stamp heartbeat, write back atomically.

    Convenience helper used by the main session whenever it touches state.json
    outside the round boundary (e.g., during alignment dialogue, status
    queries that shouldn't make this run look orphan).
    """
    if not state_path.exists():
        return
    data = json.loads(state_path.read_text())
    update_heartbeat(data)
    state_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


TERMINAL_LIFECYCLE_STATES = {"achieved", "unmet", "budget-limited", "aborted"}


def write_run_summary_if_terminal(run_dir: Path, state: dict) -> Path | None:
    """Idempotent terminal hook.

    If state.lifecycle_state is terminal, write/refresh run_summary.md and
    return its path. Otherwise no-op and return None. Idempotent: calling
    twice on the same terminal state produces the same file content.

    Phase 4: this is the orchestrator's only run_summary touchpoint. The
    actual telemetry derivation lives in run_summary.py.
    """
    if state.get("lifecycle_state") not in TERMINAL_LIFECYCLE_STATES:
        return None
    return write_run_summary(run_dir, state)
