from env_probe import probe_environment, classify_quality
from schema_validators import validate_env_json


def test_probe_returns_valid_env_json_structure():
    env = probe_environment(
        skills_list=["superpowers:brainstorming", "wiki", "discord"],
        tools_list=["ScheduleWakeup"],
    )
    assert env["schema_version"] == "v6.0"
    assert env["skills_available"]["superpowers:brainstorming"] is True
    assert env["skills_available"]["grill-me"] is False
    assert env["skills_available"]["wiki"] is True
    assert "fallback_active" in env
    assert "calibration_quality" in env


def test_classify_quality_full():
    env = {
        "skills_available": {
            "superpowers:brainstorming": True,
            "grill-me": True,
            "wiki": True,
            "codex": True,
            "grepai": True,
            "discord": True,
        }
    }
    assert classify_quality(env) == "full"


def test_classify_quality_degraded_minor():
    env = {
        "skills_available": {
            "superpowers:brainstorming": True,
            "grill-me": True,
            "wiki": True,
            "codex": True,
            "grepai": False,
            "discord": True,
        }
    }
    assert classify_quality(env) == "degraded_minor"


def test_classify_quality_degraded_major_no_alignment_skills():
    env = {
        "skills_available": {
            "superpowers:brainstorming": False,
            "grill-me": False,
            "wiki": True,
            "codex": True,
            "grepai": True,
            "discord": True,
        }
    }
    assert classify_quality(env) == "degraded_major"


def test_fallback_active_lists_missing_skills():
    env = probe_environment(
        skills_list=["wiki", "discord"],
        tools_list=["ScheduleWakeup"],
    )
    assert "superpowers:brainstorming" in env["fallback_active"]
    assert "grill-me" in env["fallback_active"]
    assert "codex" in env["fallback_active"]
    assert "grepai" in env["fallback_active"]
    assert "wiki" not in env["fallback_active"]
    assert "discord" not in env["fallback_active"]


def test_probe_output_validates_against_schema():
    env = probe_environment(
        skills_list=["superpowers:brainstorming", "wiki"],
        tools_list=["ScheduleWakeup"],
    )
    assert validate_env_json(env) is True
