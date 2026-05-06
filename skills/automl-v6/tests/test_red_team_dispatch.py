import json
import pytest
from red_team_dispatch import (
    build_red_team_prompt, parse_red_team_output, RedTeamError,
    should_trigger_red_team,
)


def test_should_trigger_red_team_via_calibrator_flag():
    calibrator_output = {"verification": {"should_red_team": True}}
    assert should_trigger_red_team(calibrator_output, force_flag=False) is True


def test_should_trigger_red_team_via_force_flag():
    calibrator_output = {"verification": {"should_red_team": False}}
    assert should_trigger_red_team(calibrator_output, force_flag=True) is True


def test_should_skip_red_team_when_neither_signal():
    calibrator_output = {"verification": {"should_red_team": False}}
    assert should_trigger_red_team(calibrator_output, force_flag=False) is False


def test_build_prompt_includes_goal():
    prompt = build_red_team_prompt(goal_md_text="# Goal: x\n\n## Acc\n1. y")
    assert "# Goal: x" in prompt
    assert "{{goal_md_text}}" not in prompt


def test_parse_valid_pass_output():
    output = json.dumps({
        "schema_version": "v6.0",
        "round_id": 1,
        "findings": [],
        "blind_spots": [],
        "verdict": "PASS",
    })
    result = parse_red_team_output(output)
    assert result["verdict"] == "PASS"


def test_parse_valid_blocked_output():
    output = json.dumps({
        "schema_version": "v6.0",
        "round_id": 1,
        "findings": [
            {"criterion_id": "c1", "gaming_approach": "stub returns true",
             "likelihood": "high", "evidence_of_gameability": "...",
             "suggested_hardening": "check return value"}
        ],
        "blind_spots": [],
        "verdict": "BLOCKED",
    })
    result = parse_red_team_output(output)
    assert result["verdict"] == "BLOCKED"
    assert len(result["findings"]) == 1


def test_parse_invalid_raises():
    with pytest.raises(RedTeamError):
        parse_red_team_output("not json")
