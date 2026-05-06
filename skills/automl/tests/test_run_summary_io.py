from run_summary_io import parse_frontmatter


def test_parse_frontmatter_extracts_yaml_block():
    text = "---\nrun_id: r1\nlifecycle_state: achieved\n---\n\n# body\n"
    fm = parse_frontmatter(text)
    assert fm["run_id"] == "r1"
    assert fm["lifecycle_state"] == "achieved"


def test_parse_frontmatter_returns_none_for_no_frontmatter():
    assert parse_frontmatter("# just body\n") is None


def test_parse_frontmatter_returns_none_for_truncated():
    assert parse_frontmatter("---\nrun_id: r1\n# never closed\n") is None


def test_parse_frontmatter_handles_yaml_error():
    """Malformed YAML returns None, no exception."""
    assert parse_frontmatter("---\n: : invalid\n---\nbody\n") is None
