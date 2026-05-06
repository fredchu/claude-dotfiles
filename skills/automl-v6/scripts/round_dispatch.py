"""Build round subagent prompt + parse subagent output."""
import json
import re
from pathlib import Path
from schema_validators import validate_round_output, SchemaValidationError

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class RoundDispatchError(Exception):
    """Raised on round dispatch / parse / validation failure."""


def build_round_prompt(
    goal_md_text: str,
    state_delta: dict,
    budget_remaining: int,
    rounds_used: int,
    rounds_cap: int,
) -> str:
    """Build full round subagent prompt with goal + delta + continuation directive."""
    continuation = (PROMPTS_DIR / "continuation.md").read_text()
    state_delta_json = json.dumps(state_delta, indent=2, ensure_ascii=False)

    return f"""You are the /automl round executor.

GOAL (verbatim, your contract):
<<<
{goal_md_text}
>>>

LAST ROUND PROGRESS (delta only):
{state_delta_json}

BUDGET REMAINING: {budget_remaining} tokens
ROUNDS USED: {rounds_used} of {rounds_cap}

{continuation}

Your tasks this round:
1. Read goal.md acceptance_criteria
2. Identify NOT-yet-achieved criteria from state delta
3. Choose ONE focused approach
4. Edit files, run evaluator, self-audit per CONTINUATION DIRECTIVE
5. Update state criteria_progress
6. Report STRUCTURED JSON (no prose).
"""


def parse_round_output(raw: str) -> dict:
    """Parse round subagent output to validated dict.

    Raises RoundDispatchError if parse or validation fails.
    """
    fence_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", raw, re.DOTALL)
    json_text = fence_match.group(1) if fence_match else raw.strip()

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise RoundDispatchError(f"Invalid JSON: {e}")

    try:
        validate_round_output(data)
    except SchemaValidationError as e:
        raise RoundDispatchError(str(e))

    return data
