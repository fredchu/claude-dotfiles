"""Orphan recovery scan + takeover classification.

Spec: §9.6.

An orphan is a run in `paused` lifecycle whose heartbeat is older than
HEARTBEAT_STALE_ORPHAN (1 hour) -- the previous session is presumed dead.

Classification:
- autonomous mode -> silent takeover (no user prompt)
- interactive mode -> prompt user before takeover
- no orphans -> no action
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

from session_lock import HEARTBEAT_STALE_ORPHAN, can_takeover


@dataclass
class TakeoverDecision:
    silent: bool
    prompt_user: bool
    orphans: list = field(default_factory=list)


def scan_for_orphans(automl_dir: Path) -> list[dict]:
    """Find paused runs whose heartbeat exceeds the orphan threshold."""
    orphans: list[dict] = []
    if not automl_dir.exists():
        return orphans
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
        if data.get("lifecycle_state") != "paused":
            continue
        if can_takeover(data, threshold=HEARTBEAT_STALE_ORPHAN):
            orphans.append({
                "run_id": run_dir.name,
                "goal_summary": data.get("goal_summary", ""),
                "last_heartbeat": (
                    data.get("active_session", {}).get("last_heartbeat")
                    if data.get("active_session") else None
                ),
            })
    return orphans


def classify_takeover_action(mode: str, orphans: list[dict]) -> TakeoverDecision:
    """Decide silent (autonomous) vs interactive prompt vs no-op."""
    if not orphans:
        return TakeoverDecision(silent=False, prompt_user=False, orphans=[])
    if mode == "autonomous":
        return TakeoverDecision(silent=True, prompt_user=False, orphans=orphans)
    return TakeoverDecision(silent=False, prompt_user=True, orphans=orphans)
