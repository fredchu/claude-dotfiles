"""Implement /automl list — scan cwd .automl/ and render a one-line-per-run summary.

Spec §8.1: list takes no args; cwd .automl/ is the implicit target.
"""
import json
from pathlib import Path


def collect_runs(automl_dir: Path) -> list[dict]:
    """Scan automl_dir for state.json files, return one dict per run."""
    rows: list[dict] = []
    if not automl_dir.exists():
        return rows
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
        rows.append({
            "run_id": data.get("run_id", run_dir.name),
            "lifecycle_state": data.get("lifecycle_state"),
            "iterations": data.get("iterations", 0),
            "actual_tokens": data.get("tokens", {}).get("actual", 0),
        })
    return rows


def render_list(rows: list[dict]) -> str:
    """Render the cohort to a markdown table-ish text block."""
    if not rows:
        return "no runs in .automl/\n"
    header = "run_id                       state            rounds    tokens"
    lines = [header, "-" * len(header)]
    for r in rows:
        lines.append(
            f"{r['run_id']:<28} {str(r.get('lifecycle_state', '?')):<16} {r.get('iterations', 0):<9} {r.get('actual_tokens', 0)}"
        )
    return "\n".join(lines) + "\n"
