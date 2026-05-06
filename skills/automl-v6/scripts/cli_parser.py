"""Parse /automl-v6 <args> into structured command.

Phase 1 supports: invoke, status, list. (pause/resume/clear/history → Phase 5.)
Phase 1 flags: --no-budget, --spec <path>.
Phase 3 flags: --allow-cwd-conflict, --autonomous.
"""
from dataclasses import dataclass, field

KNOWN_SUBCOMMANDS = {"status", "list"}


class CLIParseError(Exception):
    pass


@dataclass
class ParsedCommand:
    command: str
    freeform: str = ""
    run_id: str | None = None
    flags: dict = field(default_factory=dict)
    allow_cwd_conflict: bool = False
    autonomous: bool = False


def parse_args(args: list[str]) -> ParsedCommand:
    """Parse argv-style list into ParsedCommand."""
    if not args:
        raise CLIParseError("No arguments provided")

    flags = {}
    positional = []
    allow_cwd_conflict = False
    autonomous = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--no-budget":
            flags["no_budget"] = True
            i += 1
        elif a == "--spec":
            if i + 1 >= len(args):
                raise CLIParseError("--spec requires a path argument")
            flags["spec"] = args[i + 1]
            i += 2
        elif a == "--allow-cwd-conflict":
            allow_cwd_conflict = True
            i += 1
        elif a == "--autonomous":
            autonomous = True
            i += 1
        else:
            positional.append(a)
            i += 1

    if not positional and "spec" in flags:
        return ParsedCommand(
            command="invoke", freeform="", flags=flags,
            allow_cwd_conflict=allow_cwd_conflict, autonomous=autonomous,
        )

    if not positional:
        raise CLIParseError("Missing freeform goal description or subcommand")

    first = positional[0]
    if first in KNOWN_SUBCOMMANDS:
        run_id = positional[1] if len(positional) > 1 else None
        return ParsedCommand(
            command=first, run_id=run_id, flags=flags,
            allow_cwd_conflict=allow_cwd_conflict, autonomous=autonomous,
        )

    return ParsedCommand(
        command="invoke",
        freeform=" ".join(positional),
        flags=flags,
        allow_cwd_conflict=allow_cwd_conflict,
        autonomous=autonomous,
    )
