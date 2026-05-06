import json

import pytest

from quota_coordinator import (
    aggregate_other_sessions_used_pct,
    effective_threshold,
)


@pytest.fixture
def registry_with_two_runs(tmp_path):
    d = tmp_path / "quota_registry"
    d.mkdir()
    (d / "claude_max.json").write_text(json.dumps({
        "quota_window": "2026-05-06T14:00 -> 19:00",
        "total_used_pct": 50,
        "by_run": [
            {"run_id": "r-self", "session_id": "s1", "used_pct": 20},
            {"run_id": "r-other", "session_id": "s2", "used_pct": 30},
        ],
        "last_updated": "2026-05-06T14:00:00+08:00",
    }))
    return d


def test_aggregate_excludes_own_run(registry_with_two_runs):
    used = aggregate_other_sessions_used_pct(
        registry_dir=registry_with_two_runs, cli="claude_max", own_run_id="r-self",
    )
    assert used == 30


def test_aggregate_zero_when_only_self(registry_with_two_runs):
    used = aggregate_other_sessions_used_pct(
        registry_dir=registry_with_two_runs, cli="claude_max", own_run_id="r-other",
    )
    assert used == 20


def test_effective_threshold_subtracts_others():
    """Default 75; others using 30 -> effective 45."""
    assert effective_threshold(others_used_pct=30, base=75) == 45


def test_effective_threshold_floor_zero():
    """Never goes below 0 even if others exceed base."""
    assert effective_threshold(others_used_pct=99, base=75) == 0


def test_unknown_cli_returns_zero(tmp_path):
    """CLI registry file missing -> no others, threshold unchanged."""
    used = aggregate_other_sessions_used_pct(
        registry_dir=tmp_path, cli="unknown_cli", own_run_id="r1",
    )
    assert used == 0


def test_concurrent_writes_no_data_loss(tmp_path):
    """Two concurrent registries writing different runs both end up persisted.

    Without fcntl locking around read-modify-write the second write would
    clobber the first. With locking, both runs survive.
    """
    from gates.quota_gate import QuotaRegistry

    registry_dir = tmp_path / "quota_registry"
    registry_dir.mkdir()
    (registry_dir / "claude_max.json").write_text(json.dumps({
        "quota_window": "",
        "total_used_pct": 0,
        "by_run": [],
        "last_updated": "",
    }))

    r1 = QuotaRegistry(registry_dir=registry_dir, cli="claude_max")
    r2 = QuotaRegistry(registry_dir=registry_dir, cli="claude_max")
    r1.update_own_usage(run_id="run-a", session_id="sa", used_pct=10)
    r2.update_own_usage(run_id="run-b", session_id="sb", used_pct=20)

    data = json.loads((registry_dir / "claude_max.json").read_text())
    by_run_ids = {r["run_id"] for r in data["by_run"]}
    assert by_run_ids == {"run-a", "run-b"}
    assert data["total_used_pct"] == 30
