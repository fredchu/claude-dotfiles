import pytest
from cli_parser import parse_args, CLIParseError


def test_parse_freeform_invocation():
    cmd = parse_args(["Fix the auth bug in token refresh"])
    assert cmd.command == "invoke"
    assert cmd.freeform == "Fix the auth bug in token refresh"
    assert cmd.flags == {}


def test_parse_status_command():
    cmd = parse_args(["status"])
    assert cmd.command == "status"
    assert cmd.run_id is None


def test_parse_status_with_run_id():
    cmd = parse_args(["status", "20260506-143022-a8f3"])
    assert cmd.command == "status"
    assert cmd.run_id == "20260506-143022-a8f3"


def test_parse_list_command():
    cmd = parse_args(["list"])
    assert cmd.command == "list"


def test_parse_invocation_with_no_budget_flag():
    cmd = parse_args(["--no-budget", "Refactor X"])
    assert cmd.command == "invoke"
    assert cmd.freeform == "Refactor X"
    assert cmd.flags["no_budget"] is True


def test_parse_invocation_with_spec_flag():
    cmd = parse_args(["--spec", "/path/to/goal.md"])
    assert cmd.command == "invoke"
    assert cmd.flags["spec"] == "/path/to/goal.md"


def test_parse_empty_args_raises():
    with pytest.raises(CLIParseError):
        parse_args([])


def test_parse_unknown_subcommand_treated_as_freeform():
    cmd = parse_args(["FixSomeBug"])
    assert cmd.command == "invoke"
    assert cmd.freeform == "FixSomeBug"
