"""Parse /automl-v6 <args> into structured command.

Phase 1 supports: invoke, status, list. (pause/resume/clear/history → Phase 5.)
Flags: --no-budget, --spec <path>. (Others → Phase 2+.)
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


def parse_args(args: list[str]) -> ParsedCommand:
    """Parse argv-style list into ParsedCommand."""
    if not args:
        raise CLIParseError("No arguments provided")

    flags = {}
    positional = []
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
        else:
            positional.append(a)
            i += 1

    if not positional and "spec" in flags:
        return ParsedCommand(command="invoke", freeform="", flags=flags)

    if not positional:
        raise CLIParseError("Missing freeform goal description or subcommand")

    first = positional[0]
    if first in KNOWN_SUBCOMMANDS:
        run_id = positional[1] if len(positional) > 1 else None
        return ParsedCommand(command=first, run_id=run_id, flags=flags)

    return ParsedCommand(
        command="invoke",
        freeform=" ".join(positional),
        flags=flags,
    )
