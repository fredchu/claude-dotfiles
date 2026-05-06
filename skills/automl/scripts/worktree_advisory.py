"""Concurrent same-cwd run detection + worktree refuse message.

Spec: §9.5 decision matrix.
- Inside a worktree -> proceed (user already isolated)
- Same cwd has active /automl run -> refuse unless --allow-cwd-conflict
- No active runs -> proceed

Orphans (paused + heartbeat > 1h) do NOT count as concurrent — they belong
to dead sessions and the orphan recovery path should reclaim them rather
than block a new start.
"""
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from session_lock import HEARTBEAT_STALE_ORPHAN, can_takeover

TERMINAL_STATES = {"achieved", "unmet", "budget-limited", "aborted"}


@dataclass
class CwdConflictDecision:
    refuse: bool
    warning: bool = False
    message: str = ""
    active_runs: list = field(default_factory=list)


def is_inside_worktree(cwd: Path) -> bool:
    """True iff cwd is a git worktree (a separate checkout from the main repo).

    Uses `git rev-parse --git-dir` vs `--git-common-dir`: in a worktree these
    differ (per-worktree gitdir vs shared common dir). Returns False if cwd is
    not a git repo at all.
    """
    try:
        gd = subprocess.check_output(
            ["git", "rev-parse", "--git-dir"], cwd=cwd, text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        cd = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"], cwd=cwd, text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

    cwd_path = Path(cwd)
    gd_abs = (cwd_path / gd).resolve() if not Path(gd).is_absolute() else Path(gd).resolve()
    cd_abs = (cwd_path / cd).resolve() if not Path(cd).is_absolute() else Path(cd).resolve()
    return gd_abs != cd_abs


def find_active_runs_in_cwd(automl_dir: Path) -> list[dict]:
    """Scan .automl/<run_id>/state.json -- return non-terminal, non-orphan runs.

    A run is treated as "active" (and therefore blocking concurrent starts)
    when it's non-terminal AND its session heartbeat is fresh enough that the
    orphan-recovery path won't reclaim it. This keeps the cwd-advisory focused
    on real conflicts: two live sessions racing on the same cwd.
    """
    actives = []
    if not automl_dir.exists():
        return actives
    for run_dir in sorted(automl_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        state_path = run_dir / "state.json"
        if not state_path.exists():
            continue
        try:
            data = json.loads(state_path.read_text())
        except json.JSONDecodeError:
            continue
        if data.get("lifecycle_state") in TERMINAL_STATES:
            continue
        # Orphan = takeover-eligible by orphan threshold; not a real concurrent peer.
        if can_takeover(data, threshold=HEARTBEAT_STALE_ORPHAN):
            continue
        actives.append({
            "run_id": run_dir.name,
            "lifecycle_state": data.get("lifecycle_state"),
            "active_session": data.get("active_session"),
            "goal_summary": data.get("goal_summary", ""),
        })
    return actives


def refuse_message(active_runs: list[dict]) -> str:
    lines = ["Error: Concurrent /automl run detected in this directory", ""]
    lines.append("Active run(s):")
    for r in active_runs:
        lines.append(f"  {r['run_id']}   {r.get('lifecycle_state', '?')}")
        if r.get("goal_summary"):
            lines.append(f"    Goal: {r['goal_summary']}")
    lines += [
        "",
        "Editing the same files from two concurrent runs causes merge conflicts mid-run.",
        "",
        "Recommended (creates isolated workspace):",
        "  git worktree add ../<repo>-run2 main",
        "  cd ../<repo>-run2",
        "  /automl <goal>",
        "",
        "Or override (high collision risk, not recommended):",
        "  /automl <goal> --allow-cwd-conflict",
    ]
    return "\n".join(lines)


def check_cwd_conflict(
    cwd: Path, automl_dir: Path, allow_override: bool,
) -> CwdConflictDecision:
    """Decide whether to proceed, warn-and-proceed, or refuse."""
    if is_inside_worktree(cwd):
        return CwdConflictDecision(refuse=False)
    actives = find_active_runs_in_cwd(automl_dir)
    if not actives:
        return CwdConflictDecision(refuse=False)
    if allow_override:
        return CwdConflictDecision(
            refuse=False,
            warning=True,
            active_runs=actives,
            message=f"WARNING: proceeding with --allow-cwd-conflict; {len(actives)} active run(s)",
        )
    return CwdConflictDecision(
        refuse=True,
        message=refuse_message(actives),
        active_runs=actives,
    )
