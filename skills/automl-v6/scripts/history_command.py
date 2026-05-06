"""Implement /automl history — show calibrator telemetry across runs.

Spec §8.1: history reads run_summary.md frontmatter from cwd .automl/.
This is the per-user query surface — separate from the launchd
calibrator_review job (which reports drift across all of ~/.automl/).
"""
from pathlib import Path

from run_summary_io import parse_frontmatter


def collect_history(automl_dir: Path) -> list[dict]:
    """Read run_summary.md from each run dir, extract calibrator_telemetry rows."""
    rows: list[dict] = []
    if not automl_dir.exists():
        return rows
    for run_dir in sorted(automl_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        path = run_dir / "run_summary.md"
        if not path.exists():
            continue
        fm = parse_frontmatter(path.read_text())
        if not fm:
            continue
        telemetry = fm.get("calibrator_telemetry", {})
        rows.append({
            "run_id": fm.get("run_id", run_dir.name),
            "lifecycle_state": fm.get("lifecycle_state"),
            "iterations": fm.get("iterations", 0),
            "terminal_ts": fm.get("terminal_ts"),
            "estimated_tokens": telemetry.get("estimated_tokens"),
            "actual_tokens": telemetry.get("actual_tokens"),
            "diff_pct": telemetry.get("diff_pct"),
        })
    return rows


def render_history(rows: list[dict]) -> str:
    if not rows:
        return "no runs with run_summary.md in .automl/\n"
    header = "run_id                       state            est tokens    actual    diff_pct  terminal_ts"
    lines = [header, "-" * len(header)]
    for r in rows:
        lines.append(
            f"{r['run_id']:<28} {str(r.get('lifecycle_state','?')):<16} {str(r.get('estimated_tokens','?')):<13} "
            f"{str(r.get('actual_tokens','?')):<9} {str(r.get('diff_pct','?')):<9} {r.get('terminal_ts','?')}"
        )
    return "\n".join(lines) + "\n"
