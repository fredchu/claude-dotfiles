"""Parse and write goal.md (markdown body + YAML frontmatter)."""
import re
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


class GoalIOError(Exception):
    """Raised on goal.md parse, write, or validation failure."""


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def _load_frontmatter_schema() -> dict:
    schema_path = SCHEMAS_DIR / "goal_md.schema.yaml"
    return yaml.safe_load(schema_path.read_text())


def parse_goal_md(path: Path) -> tuple[dict, str]:
    """Parse goal.md into (frontmatter_dict, body_str).

    Raises GoalIOError if frontmatter format invalid or schema mismatch.
    """
    if not path.exists():
        raise GoalIOError(f"goal.md not found at {path}")

    text = path.read_text()
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise GoalIOError("goal.md missing valid frontmatter (---...---)")

    fm_text, body = m.group(1), m.group(2).lstrip("\n")
    try:
        frontmatter = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        raise GoalIOError(f"YAML parse error in frontmatter: {e}")

    schema = _load_frontmatter_schema()
    try:
        validate(instance=frontmatter, schema=schema)
    except ValidationError as e:
        raise GoalIOError(
            f"goal.md frontmatter invalid: {e.message} at {list(e.absolute_path)}"
        )

    return frontmatter, body


def write_goal_md(path: Path, frontmatter: dict, body: str) -> None:
    """Write goal.md with validated frontmatter + body."""
    schema = _load_frontmatter_schema()
    try:
        validate(instance=frontmatter, schema=schema)
    except ValidationError as e:
        raise GoalIOError(
            f"frontmatter invalid: {e.message} at {list(e.absolute_path)}"
        )

    fm_text = yaml.safe_dump(
        frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False
    )
    content = f"---\n{fm_text}---\n\n{body}"
    path.write_text(content)
