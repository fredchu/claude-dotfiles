import json
import pytest
from calibrator_dispatch import (
    build_calibrator_prompt, parse_calibrator_output, CalibratorError
)
from conftest import FIXTURES_DIR


def test_build_prompt_substitutes_variables():
    prompt = build_calibrator_prompt(
        user_input="Fix the auth bug",
        cwd="/Users/fred/proj",
        git_context="* abc123 latest commit",
        similar_runs_summary="No similar runs",
        wiki_lessons_summary="No relevant lessons",
    )
    assert "Fix the auth bug" in prompt
    assert "/Users/fred/proj" in prompt
    assert "abc123" in prompt
    assert "{{user_input}}" not in prompt


def test_parse_valid_calibrator_output():
    fixture = json.loads(
        (FIXTURES_DIR / "sample_calibrator_outputs/valid_simple.json").read_text()
    )
    result = parse_calibrator_output(json.dumps(fixture))
    assert result["calibrator_confidence"] == 0.85
    assert result["alignment"]["dialogue_depth"] == "shallow"


def test_parse_invalid_calibrator_output_raises():
    fixture = json.loads(
        (FIXTURES_DIR / "sample_calibrator_outputs/invalid_no_criteria.json").read_text()
    )
    with pytest.raises(CalibratorError):
        parse_calibrator_output(json.dumps(fixture))


def test_parse_non_json_raises():
    with pytest.raises(CalibratorError):
        parse_calibrator_output("not json {{{")


def test_parse_extracts_json_from_code_block():
    fixture = json.loads(
        (FIXTURES_DIR / "sample_calibrator_outputs/valid_simple.json").read_text()
    )
    wrapped = f"```json\n{json.dumps(fixture)}\n```"
    result = parse_calibrator_output(wrapped)
    assert result["calibrator_confidence"] == 0.85
