import pytest
from goal_io import parse_goal_md, write_goal_md, GoalIOError


VALID_GOAL_MD = """---
run_id: 20260506-143022-test
schema_version: v6.0
calibrator:
  dialogue_depth: normal
  budget_estimate: 80000
  budget_strategy: hard
  confidence: 0.85
acceptance_criteria:
  - id: c1
    desc: "Bug A reproduces in failing test, then passes after fix"
    verification: "pytest tests/auth/test_a.py -v"
  - id: c2
    desc: "Token refresh edge case has new test"
    verification: "pytest tests/auth/test_token.py::test_refresh -v"
---

# Goal: Improve auth module reliability

## Outcome
Reduce 401 errors by fixing 3 known auth bugs.

## Scope
- Touch: src/auth/, tests/auth/

## Acceptance Criteria
1. Bug A reproduces in failing test, then passes after fix
2. Token refresh edge case has new test

## Verification
`pytest tests/auth/ -v`

## Stop Rules
- Touching src/billing/ → halt
"""


def test_parse_goal_md_returns_frontmatter_and_body(tmp_path):
    goal_path = tmp_path / "goal.md"
    goal_path.write_text(VALID_GOAL_MD)
    frontmatter, body = parse_goal_md(goal_path)
    assert frontmatter["run_id"] == "20260506-143022-test"
    assert len(frontmatter["acceptance_criteria"]) == 2
    assert frontmatter["acceptance_criteria"][0]["id"] == "c1"
    assert "# Goal: Improve auth module reliability" in body
    assert "## Outcome" in body


def test_parse_goal_md_rejects_invalid_frontmatter(tmp_path):
    bad_md = """---
run_id: invalid_format
schema_version: v6.0
---

# Goal: x
"""
    goal_path = tmp_path / "goal.md"
    goal_path.write_text(bad_md)
    with pytest.raises(GoalIOError):
        parse_goal_md(goal_path)


def test_parse_goal_md_rejects_missing_acceptance_criteria(tmp_path):
    bad_md = """---
run_id: 20260506-143022-test
schema_version: v6.0
calibrator:
  dialogue_depth: normal
  budget_estimate: 80000
  budget_strategy: hard
  confidence: 0.85
---

# Goal: x
"""
    goal_path = tmp_path / "goal.md"
    goal_path.write_text(bad_md)
    with pytest.raises(GoalIOError):
        parse_goal_md(goal_path)


def test_write_goal_md_round_trip(tmp_path):
    frontmatter = {
        "run_id": "20260506-143022-test",
        "schema_version": "v6.0",
        "calibrator": {
            "dialogue_depth": "normal",
            "budget_estimate": 80000,
            "budget_strategy": "hard",
            "confidence": 0.85,
        },
        "acceptance_criteria": [
            {"id": "c1", "desc": "test desc", "verification": "pytest"}
        ],
    }
    body = "# Goal: test\n\n## Outcome\nTest outcome\n"
    goal_path = tmp_path / "goal.md"
    write_goal_md(goal_path, frontmatter, body)
    fm2, body2 = parse_goal_md(goal_path)
    assert fm2 == frontmatter
    assert "# Goal: test" in body2
