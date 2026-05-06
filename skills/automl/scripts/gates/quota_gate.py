"""Quota gate — per-CLI registry.

Phase 2: single-session.
Phase 3: fcntl lock around update_own_usage so concurrent sessions don't lose
data. Cross-session aggregation lives in `quota_coordinator`.
"""
import fcntl
import json
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_THRESHOLD = 75
SUPPORTED_CLIS = {"claude_max", "codex_chatgpt_plus"}


@dataclass
class QuotaGateResult:
    tripped: bool
    target_state: str | None = None
    pause_reason: str | None = None
    reason: str = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def check_quota(
    registry_dir: Path, cli: str, run_id: str, own_used_pct: float,
    threshold: int | None = None,
) -> QuotaGateResult:
    """Trip if own_used_pct >= effective threshold for known CLI.

    If `threshold` is provided, it overrides cross-session aggregation
    (legacy single-session behavior). Otherwise the gate consults
    `quota_coordinator.aggregate_other_sessions_used_pct` and uses the
    effective threshold (`75 - others_used`).
    """
    if cli not in SUPPORTED_CLIS:
        return QuotaGateResult(tripped=False)

    if threshold is None:
        from quota_coordinator import (
            aggregate_other_sessions_used_pct,
            effective_threshold,
        )
        others = aggregate_other_sessions_used_pct(registry_dir, cli, run_id)
        active_threshold = effective_threshold(others, base=DEFAULT_THRESHOLD)
    else:
        active_threshold = threshold

    if own_used_pct >= active_threshold:
        return QuotaGateResult(
            tripped=True,
            target_state="paused",
            pause_reason="quota_wait",
            reason=f"{cli} quota usage {own_used_pct}% >= {active_threshold}%",
        )
    return QuotaGateResult(tripped=False)


class QuotaRegistry:
    """Per-CLI quota registry stored at ~/.automl/quota_registry/{cli}.json."""

    def __init__(self, registry_dir: Path, cli: str):
        self.registry_dir = registry_dir
        self.cli = cli
        self.path = registry_dir / f"{cli}.json"

    def read(self) -> dict:
        if not self.path.exists():
            return {
                "quota_window": "",
                "total_used_pct": 0,
                "by_run": [],
                "last_updated": _now_iso(),
            }
        return json.loads(self.path.read_text())

    def update_own_usage(self, run_id: str, session_id: str, used_pct: float) -> None:
        """Insert or update this run's usage entry; recompute total.

        Holds an exclusive fcntl lock on a sidecar `.lock` file across the
        read-modify-write so concurrent updaters do not clobber each other.
        """
        with _locked_path(self.path):
            data = self.read()
            by_run = [r for r in data.get("by_run", []) if r.get("run_id") != run_id]
            by_run.append({"run_id": run_id, "session_id": session_id, "used_pct": used_pct})
            data["by_run"] = by_run
            data["total_used_pct"] = sum(r.get("used_pct", 0) for r in by_run)
            data["last_updated"] = _now_iso()
            self.path.write_text(json.dumps(data, indent=2))


@contextmanager
def _locked_path(path: Path):
    """Hold an exclusive fcntl lock on a sidecar file while updating registry."""
    lock_path = path.with_suffix(".lock")
    lock_path.touch(exist_ok=True)
    with open(lock_path, "r+") as fp:
        fcntl.flock(fp.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fp.fileno(), fcntl.LOCK_UN)
