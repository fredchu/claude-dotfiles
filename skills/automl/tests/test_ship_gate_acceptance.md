# /automl v6.0 Ship Acceptance Gate (spec §11.5)

This document is a literal verification pass. For each item, the
authoritative test or manual procedure is named. Run all named tests
green before declaring v6.0 GA.

| # | Acceptance criterion | Verified by |
|---|---|---|
| 1 | CC adapter completes 5 sample tasks (bug_fix / refactor / docs / feature / research) | Manual: 5 dogfood runs, log run_id + outcome here |
| 2 | Calibrator accuracy median \|diff_pct\| < 50% (acceptable baseline) | `For_Claude/scripts/calibrator_review/calibrator_review.py --no-alert` after dogfood; report should show median \|diff_pct\| < 50% |
| 3 | Failure injection: every edge case in spec §10 catalog has corresponding test | `tests/` matches §10 catalog ~21 cases (Phases 1-5 tests cover most; gap audit needed during ship review) |
| 4 | `/automl-legacy` parallel install no conflict with v6 | `ls ~/.claude/skills/automl-legacy/` exists; `/automl-legacy --help` works; `/automl --help` (v6) works |
| 5 | Status display correct in `--no-budget` / fallback / quota_wait states | `tests/test_status_renderer.py` covers all three; manual inspection of `/automl status` output for an active run |
| 6 | Audit rejects false-achieved at least 1 real case | `tests/test_audit_gatekeeper.py` (Phase 1) covers the rejection path; need ≥1 real-run case from dogfood |
| 7 | Multi-session lock test (same-cwd second session refused correctly) | `tests/e2e/test_concurrent_cwd_refused.py` (Phase 3) |
| 8 | Quota registry per-CLI isolation test | `tests/gates/test_quota_gate.py::test_unknown_cli_returns_pass` and `tests/test_quota_coordinator.py` (Phase 2 + 3) |
| 9 | Worktree integration test (refuse message correct, in-worktree run works) | `tests/test_worktree_advisory.py::test_is_inside_worktree_added` and `tests/e2e/test_concurrent_cwd_refused.py` (Phase 3) |
| 10 | Orphan takeover test (autonomous silent, interactive prompt) | `tests/e2e/test_orphan_autonomous_takeover.py` and `tests/e2e/test_cross_session_takeover.py` (Phase 3) |

## How to run

```bash
cd ~/.claude/skills/automl && python3 -m pytest tests/ -q
```

All Phase 1+2+3+4+5 tests must pass green. Items 1, 2, and 6 also require
≥5 dogfood runs to populate evidence — log run_ids in this file before
declaring GA.

## Dogfood log (filled during ship)

(empty — populate as v6.0 dogfood runs complete)
