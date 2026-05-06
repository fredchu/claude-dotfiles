"""RED_TEAM subagent dispatch + main-session repair loop."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from schema_validators import validate_red_team_output, SchemaValidationError

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
MAX_REPAIR_CYCLES = 2


class RedTeamError(Exception):
    """Raised when RED_TEAM output cannot be parsed or fails schema validation."""


def should_trigger_red_team(calibrator_output: dict, force_flag: bool = False) -> bool:
    """Decide whether to dispatch RED_TEAM."""
    if force_flag:
        return True
    return calibrator_output.get("verification", {}).get("should_red_team", False)


def build_red_team_prompt(goal_md_text: str) -> str:
    """Substitute goal text into RED_TEAM prompt template."""
    template = (PROMPTS_DIR / "red_team.md").read_text()
    return template.replace("{{goal_md_text}}", goal_md_text)


def parse_red_team_output(raw: str) -> dict:
    """Parse RED_TEAM subagent output into a validated dict."""
    fence_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", raw, re.DOTALL)
    json_text = fence_match.group(1) if fence_match else raw.strip()

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise RedTeamError(f"Invalid JSON: {e}")

    try:
        validate_red_team_output(data)
    except SchemaValidationError as e:
        raise RedTeamError(str(e))

    return data


def record_red_team_invocation(state: dict, round_id: int, verdict: str, rationale: str = "") -> None:
    """Append a RED_TEAM invocation record to state.

    Phase 5: replaces the Phase 4 audit-log proxy. Called by main session
    immediately after parse_red_team_output succeeds.
    """
    if verdict not in {"approved", "blocked", "advisory"}:
        raise ValueError(f"verdict must be approved|blocked|advisory, got {verdict!r}")
    state.setdefault("red_team_invocations", []).append({
        "round_id": round_id,
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "verdict": verdict,
        "rationale": rationale,
    })
