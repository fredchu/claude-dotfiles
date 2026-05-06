"""Build + write the frozen run_summary.md at terminal lifecycle.

Phase 4 telemetry capture. The run_summary.md is the single source of truth
read by calibrator_review.py to compute drift across runs.
"""
import json
from pathlib import Path

import yaml


def build_calibrator_telemetry(calibrator: dict, state: dict) -> dict:
    """Compute the 8-field telemetry block from calibrator.json + state.json.

    Fields with no source resolve to None (review job tolerates missing data).
    """
    estimated = calibrator.get("budget", {}).get("estimated_tokens", 0)
    actual = state.get("tokens", {}).get("actual", 0)

    if estimated > 0:
        diff_pct = round((actual - estimated) / estimated * 100)
    else:
        diff_pct = None

    alignment_meta = state.get("alignment_metadata") or {}
    questions_asked = alignment_meta.get("questions_asked")
    actual_depth = alignment_meta.get("depth")

    estimated_should_red_team = calibrator.get("verification", {}).get("should_red_team", False)
    audit_log = state.get("audit_failure_log", [])
    red_team_invoked = any(entry.get("red_team_invoked") for entry in audit_log)
    red_team_skipped = not red_team_invoked

    return {
        "estimated_tokens": estimated,
        "actual_tokens": actual,
        "diff_pct": diff_pct,
        "estimated_dialogue_depth": calibrator.get("alignment", {}).get("dialogue_depth"),
        "actual_dialogue_depth": actual_depth,
        "actual_questions_asked": questions_asked,
        "estimated_should_red_team": estimated_should_red_team,
        "red_team_skipped": red_team_skipped,
        "red_team_was_needed_in_hindsight": None,
    }


def build_run_summary_md(calibrator: dict, state: dict) -> str:
    """Render frontmatter + body markdown. Frozen format for parser compatibility."""
    telemetry = build_calibrator_telemetry(calibrator, state)
    final_transition = next(
        (t for t in reversed(state.get("lifecycle_transitions", [])) if t.get("to") in {"achieved", "unmet", "budget-limited", "aborted"}),
        None,
    )
    frontmatter = {
        "schema_version": "v6.0",
        "run_id": state["run_id"],
        "lifecycle_state": state["lifecycle_state"],
        "iterations": state.get("iterations", 0),
        "terminal_ts": final_transition["ts"] if final_transition else None,
        "calibrator_telemetry": telemetry,
    }
    body_lines = [
        "---",
        yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).rstrip(),
        "---",
        "",
        f"# Run summary — {state['run_id']}",
        "",
        f"Final lifecycle: **{state['lifecycle_state']}**  ",
        f"Iterations: {state.get('iterations', 0)}  ",
        f"Tokens: {telemetry['actual_tokens']} actual / {telemetry['estimated_tokens']} estimated"
        + (f" ({telemetry['diff_pct']:+d}%)" if telemetry["diff_pct"] is not None else " (no estimate)"),
        "",
        "## Criteria outcome",
        "",
    ]
    for cid, prog in state.get("criteria_progress", {}).items():
        body_lines.append(f"- `{cid}`: {prog.get('status', 'unknown')}")
    body_lines.append("")
    return "\n".join(body_lines)


def write_run_summary(run_dir: Path, state: dict) -> Path:
    """Read calibrator.json + state -> write run_summary.md (overwrite if exists).

    Returns the path written. Caller is responsible for ensuring this is only
    invoked once per terminal transition (orchestrator hook gates on lifecycle).
    """
    calibrator_path = run_dir / "calibrator.json"
    if not calibrator_path.exists():
        raise FileNotFoundError(f"calibrator.json not found at {calibrator_path}")
    calibrator = json.loads(calibrator_path.read_text())

    md = build_run_summary_md(calibrator, state)
    out = run_dir / "run_summary.md"
    out.write_text(md)
    return out
