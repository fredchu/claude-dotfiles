"""Parse /automl-v6 <args> into structured command.

Phase 1 supports: invoke, status, list. (pause/resume/clear/history → Phase 5.)
Phase 1 flags: --no-budget, --spec <path>.
Phase 3 flags: --allow-cwd-conflict, --autonomous.
"""
from dataclasses import dataclass, field

KNOWN_SUBCOMMANDS = {"status", "list", "pause", "resume", "clear", "history"}
DEPTH_VALUES = {"shallow", "normal", "deep"}
CLI_VALUES = {"claude", "codex", "gemini"}


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
        elif a == "--budget":
            if i + 1 >= len(args):
                raise CLIParseError("--budget requires an integer argument")
            try:
                flags["budget_override"] = int(args[i + 1])
            except ValueError:
                raise CLIParseError(f"--budget requires an integer, got {args[i + 1]!r}")
            i += 2
        elif a == "--depth":
            if i + 1 >= len(args):
                raise CLIParseError("--depth requires a value")
            value = args[i + 1]
            if value not in DEPTH_VALUES:
                raise CLIParseError(f"--depth must be one of {sorted(DEPTH_VALUES)}, got {value!r}")
            flags["depth_override"] = value
            i += 2
        elif a == "--red-team":
            flags["force_red_team"] = True
            i += 1
        elif a == "--no-red-team":
            flags["skip_red_team"] = True
            i += 1
        elif a == "--no-codex":
            flags["no_codex"] = True
            i += 1
        elif a == "--max-iter":
            if i + 1 >= len(args):
                raise CLIParseError("--max-iter requires an integer argument")
            try:
                flags["max_iter"] = int(args[i + 1])
            except ValueError:
                raise CLIParseError(f"--max-iter requires an integer, got {args[i + 1]!r}")
            i += 2
        elif a == "--max-wall":
            if i + 1 >= len(args):
                raise CLIParseError("--max-wall requires an integer argument (hours)")
            try:
                flags["max_wall_hours"] = int(args[i + 1])
            except ValueError:
                raise CLIParseError(f"--max-wall requires an integer hour count, got {args[i + 1]!r}")
            i += 2
        elif a == "--force-fallback":
            if i + 1 >= len(args):
                raise CLIParseError("--force-fallback requires a dependency name")
            flags["force_fallback"] = args[i + 1]
            i += 2
        elif a == "--cli":
            if i + 1 >= len(args):
                raise CLIParseError("--cli requires a value")
            value = args[i + 1]
            if value not in CLI_VALUES:
                raise CLIParseError(f"--cli must be one of {sorted(CLI_VALUES)}, got {value!r}")
            flags["cli"] = value
            i += 2
        else:
            positional.append(a)
            i += 1

    if flags.get("force_red_team") and flags.get("skip_red_team"):
        raise CLIParseError("--red-team and --no-red-team are mutually exclusive")

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
