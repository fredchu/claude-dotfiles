"""E2E test fixtures: mock subagent dispatch by injecting pre-canned responses."""
import json
import sys
import pytest
from pathlib import Path

# Ensure scripts/ is on path (e2e test conftest sits 2 levels deep)
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def mock_calibrator_response():
    """Returns the calibrator output (pre-canned)."""
    return json.loads((FIXTURES_DIR / "sample_calibrator_outputs/valid_simple.json").read_text())


@pytest.fixture
def mock_round_responses():
    """Returns a sequence of round subagent outputs simulating progress over rounds."""
    return [
        {
            "round_id": 1,
            "tokens_used_this_round": 5200,
            "criteria_progress_update": {
                "c1": {"status": "pursuing", "evidence": [], "next_step_attempt": "investigating"}
            },
            "blockers": [],
            "main_session_action_request": None,
        },
        {
            "round_id": 2,
            "tokens_used_this_round": 8400,
            "criteria_progress_update": {
                "c1": {
                    "status": "achieved",
                    "evidence": [
                        {"type": "file_change", "path": "src/auth/x.py:1-10", "summary": "fix"},
                        {
                            "type": "command_output",
                            "command": "pytest tests/auth/test_x.py::test_repro -v",
                            "verbatim_excerpt": "test_repro PASSED [100%]\n1 passed",
                        },
                        {
                            "type": "audit_check",
                            "criterion_verbatim": "Bug X reproduces in failing test, then passes after fix",
                            "satisfied": True,
                            "rationale": "git show HEAD~1 confirms test failed pre-fix; HEAD passes",
                        },
                    ],
                }
            },
            "blockers": [],
            "main_session_action_request": None,
        },
    ]
