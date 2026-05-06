"""Shared YAML frontmatter parser for run_summary.md files."""
import yaml


def parse_frontmatter(text: str) -> dict | None:
    """Extract the first YAML frontmatter block from a markdown string.

    Returns None for missing frontmatter, truncated frontmatter, or malformed YAML.
    """
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
