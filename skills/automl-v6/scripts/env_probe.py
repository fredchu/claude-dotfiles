"""Detect available skills and tools at /automl startup.

Output conforms to schemas/env_json.schema.json.
"""

REQUIRED_SOFT_DEPS = [
    "superpowers:brainstorming",
    "grill-me",
    "wiki",
    "codex",
    "grepai",
    "discord",
]

ALIGNMENT_SKILLS = {"superpowers:brainstorming", "grill-me"}
ROUTING_SKILLS = {"codex"}


def probe_environment(skills_list: list[str], tools_list: list[str]) -> dict:
    """Build env.json dict from detected skills and tools.

    Args:
        skills_list: skills detected as available (parsed from <system-reminder>
                     available-skills section, or other CLI's skill list).
        tools_list: tools detected as available (e.g. ["ScheduleWakeup"]).

    Returns:
        dict matching env.json schema.
    """
    skills_set = set(skills_list)
    skills_available = {dep: (dep in skills_set) for dep in REQUIRED_SOFT_DEPS}
    tools_available = {tool: True for tool in tools_list}

    fallback_active = [dep for dep, present in skills_available.items() if not present]

    env = {
        "schema_version": "v6.0",
        "skills_available": skills_available,
        "tools_available": tools_available,
        "fallback_active": fallback_active,
        "calibration_quality": "full",
    }
    env["calibration_quality"] = classify_quality(env)
    return env


def classify_quality(env: dict) -> str:
    """Classify env into 'full' / 'degraded_minor' / 'degraded_major'.

    Rules:
    - degraded_major: both alignment skills missing OR all routing skills missing
    - degraded_minor: 1-2 enhancers missing
    - full: all soft deps present
    """
    skills = env.get("skills_available", {})
    missing_alignment = [s for s in ALIGNMENT_SKILLS if not skills.get(s, False)]
    missing_routing = [s for s in ROUTING_SKILLS if not skills.get(s, False)]
    missing_total = sum(1 for v in skills.values() if not v)

    if len(missing_alignment) == len(ALIGNMENT_SKILLS):
        return "degraded_major"
    if len(missing_routing) == len(ROUTING_SKILLS):
        return "degraded_major"
    if missing_total == 0:
        return "full"
    return "degraded_minor"
