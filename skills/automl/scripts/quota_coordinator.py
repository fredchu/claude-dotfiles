"""Cross-session quota aggregation. Phase 3 extension to QuotaRegistry."""
import json
from pathlib import Path

DEFAULT_BASE_THRESHOLD = 75


def aggregate_other_sessions_used_pct(
    registry_dir: Path, cli: str, own_run_id: str,
) -> float:
    """Sum used_pct across all registered runs except own.

    Returns 0 if registry file does not exist (unknown CLI / fresh state).
    """
    path = registry_dir / f"{cli}.json"
    if not path.exists():
        return 0
    data = json.loads(path.read_text())
    return sum(
        r.get("used_pct", 0)
        for r in data.get("by_run", [])
        if r.get("run_id") != own_run_id
    )


def effective_threshold(
    others_used_pct: float, base: int = DEFAULT_BASE_THRESHOLD,
) -> int:
    """Conservative throttle: leave headroom for already-running peers."""
    return max(0, base - int(others_used_pct))
