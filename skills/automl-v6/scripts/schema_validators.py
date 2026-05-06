"""JSON Schema validators for /automl v6 artifacts."""
import json
from pathlib import Path
from jsonschema import validate, ValidationError

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


class SchemaValidationError(Exception):
    """Raised when JSON does not match its schema."""


def _load_schema(name: str) -> dict:
    schema_path = SCHEMAS_DIR / name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    return json.loads(schema_path.read_text())


def validate_state_json(data: dict) -> bool:
    """Validate state.json structure. Raises SchemaValidationError on fail."""
    schema = _load_schema("state_json.schema.json")
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        raise SchemaValidationError(
            f"state.json invalid: {e.message} at {list(e.absolute_path)}"
        )
    return True


def validate_env_json(data: dict) -> bool:
    """Validate env.json structure. Raises SchemaValidationError on fail."""
    schema = _load_schema("env_json.schema.json")
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        raise SchemaValidationError(
            f"env.json invalid: {e.message} at {list(e.absolute_path)}"
        )
    return True


def validate_calibrator_output(data: dict) -> bool:
    """Validate calibrator subagent output. Raises SchemaValidationError on fail."""
    schema = _load_schema("calibrator_output.schema.json")
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        raise SchemaValidationError(
            f"calibrator output invalid: {e.message} at {list(e.absolute_path)}"
        )
    return True


def validate_round_output(data: dict) -> bool:
    """Validate round subagent output structure. Raises SchemaValidationError on fail."""
    schema = _load_schema("round_output.schema.json")
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        raise SchemaValidationError(
            f"round output invalid: {e.message} at {list(e.absolute_path)}"
        )
    return True


def validate_red_team_output(data: dict) -> bool:
    """Validate RED_TEAM subagent output. Raises SchemaValidationError on fail."""
    schema = _load_schema("red_team_output.schema.json")
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        raise SchemaValidationError(
            f"red_team output invalid: {e.message} at {list(e.absolute_path)}"
        )
    return True
