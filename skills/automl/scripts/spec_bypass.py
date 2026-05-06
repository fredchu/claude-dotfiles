"""Implement --spec <path> bypass: init a run from existing goal.md without alignment.

Spec §8.1: /automl --spec <path> "Start from existing goal.md, skip alignment".
Lifecycle: writes aligning then immediately transitions to pursuing with
reason "spec bypass" — the alignment phase is recorded as 0 ms long, making
the bypass clear in the lifecycle audit trail.

criteria_progress is seeded from goal.md frontmatter's acceptance_criteria.
The run dir's goal.md is a copy of the spec_path's content.
"""
from datetime import datetime, timezone
from pathlib import Path

from goal_io import parse_goal_md, write_goal_md, GoalIOError
from lifecycle_fsm import transition
from state_io import init_state, read_state, write_state


class SpecBypassError(Exception):
    """Raised when --spec bypass cannot initialize a run."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def init_run_from_spec(
    spec_path: Path,
    run_dir: Path,
    session_id: str,
    pid: int,
) -> dict:
    """Initialize a run from existing goal.md; skip alignment, land in pursuing."""
    if not spec_path.exists():
        raise SpecBypassError(f"spec goal.md not found at {spec_path}")
    try:
        frontmatter, body = parse_goal_md(spec_path)
    except GoalIOError as e:
        raise SpecBypassError(f"goal.md invalid: {e}") from e

    run_id = frontmatter["run_id"]

    if run_dir.exists() and (run_dir / "state.json").exists():
        raise SpecBypassError(f"run_dir already initialized: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)

    # Copy goal.md into run_dir (run owns its goal.md)
    write_goal_md(run_dir / "goal.md", frontmatter, body)

    # Init state in aligning (re-uses existing helper for consistency)
    init_state(run_dir, run_id=run_id, session_id=session_id, pid=pid)
    state = read_state(run_dir)

    # Transition aligning -> pursuing (FSM validates)
    transition("aligning", "pursuing", reason="spec bypass")
    state["lifecycle_state"] = "pursuing"
    state["lifecycle_transitions"].append({
        "from": "aligning",
        "to": "pursuing",
        "ts": _now_iso(),
        "reason": "spec bypass: started from existing goal.md",
    })

    # Seed criteria_progress from frontmatter
    state["criteria_progress"] = {
        c["id"]: {"status": "pending", "evidence": []}
        for c in frontmatter["acceptance_criteria"]
    }

    write_state(run_dir, state)
    return state
