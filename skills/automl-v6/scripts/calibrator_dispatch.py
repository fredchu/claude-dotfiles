"""Build calibrator subagent prompt + parse subagent output."""
import json
import re
from pathlib import Path
from schema_validators import validate_calibrator_output, SchemaValidationError

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


class CalibratorError(Exception):
    """Raised on calibrator dispatch / parse / validation failure."""


def build_calibrator_prompt(
    user_input: str,
    cwd: str,
    git_context: str,
    similar_runs_summary: str,
    wiki_lessons_summary: str,
) -> str:
    """Substitute template variables into calibrator prompt."""
    template = (PROMPTS_DIR / "calibrator.md").read_text()
    schema = (SCHEMAS_DIR / "calibrator_output.schema.json").read_text()

    return (
        template
        .replace("{{user_input}}", user_input)
        .replace("{{cwd}}", cwd)
        .replace("{{git_context}}", git_context)
        .replace("{{similar_runs_summary}}", similar_runs_summary)
        .replace("{{wiki_lessons_summary}}", wiki_lessons_summary)
        .replace("{{output_schema}}", schema)
    )


def parse_calibrator_output(raw: str) -> dict:
    """Parse subagent output (may be wrapped in code fence) to validated dict.

    Raises CalibratorError if parse or validation fails.
    """
    fence_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", raw, re.DOTALL)
    json_text = fence_match.group(1) if fence_match else raw.strip()

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise CalibratorError(f"Invalid JSON: {e}")

    try:
        validate_calibrator_output(data)
    except SchemaValidationError as e:
        raise CalibratorError(str(e))

    return data
