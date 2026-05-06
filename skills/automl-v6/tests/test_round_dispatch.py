import pytest
from round_dispatch import (
    build_round_prompt, parse_round_output, RoundDispatchError
)
from conftest import FIXTURES_DIR


def test_build_round_prompt_includes_goal_and_state():
    goal_md = "# Goal: test\n\n## Acceptance\n1. c1 desc\n"
    state_delta = {"c1": {"status": "pursuing"}}
    prompt = build_round_prompt(
        goal_md_text=goal_md,
        state_delta=state_delta,
        budget_remaining=47200,
        rounds_used=2,
        rounds_cap=5,
    )
    assert "# Goal: test" in prompt
    assert "47200" in prompt
    assert "pursuing" in prompt
    assert "CONTINUATION DIRECTIVE" in prompt


def test_parse_valid_achieved_output():
    fixture = (FIXTURES_DIR / "sample_round_outputs/valid_achieved.json").read_text()
    result = parse_round_output(fixture)
    assert result["criteria_progress_update"]["c1"]["status"] == "achieved"
    assert len(result["criteria_progress_update"]["c1"]["evidence"]) == 3


def test_parse_valid_pursuing_output():
    fixture = (FIXTURES_DIR / "sample_round_outputs/valid_pursuing.json").read_text()
    result = parse_round_output(fixture)
    assert result["criteria_progress_update"]["c1"]["status"] == "pursuing"


def test_parse_invalid_json_raises():
    with pytest.raises(RoundDispatchError):
        parse_round_output("not valid json {{")
