"""Audit gatekeeper: validate round subagent's `achieved` claims have full evidence."""
from dataclasses import dataclass, field

REQUIRED_EVIDENCE_TYPES = {"file_change", "command_output", "audit_check"}


@dataclass
class AuditFailure:
    criterion_id: str
    reason: str


@dataclass
class AuditResult:
    all_pass: bool
    audit_failures: list[AuditFailure] = field(default_factory=list)


def _evidence_types_present(evidence: list[dict]) -> set[str]:
    return {e.get("type") for e in evidence}


def _find_audit_check(evidence: list[dict]) -> dict | None:
    for e in evidence:
        if e.get("type") == "audit_check":
            return e
    return None


def audit_round_output(output: dict) -> AuditResult:
    """Validate every `achieved` claim in round output has full evidence.

    Rules:
    - status != "achieved" → no audit required (pass automatically)
    - status == "achieved" → must have all 3 evidence types
    - status == "achieved" + audit_check.satisfied is False → fail
    """
    failures: list[AuditFailure] = []
    progress = output.get("criteria_progress_update", {})

    for cid, criterion in progress.items():
        if criterion.get("status") != "achieved":
            continue

        evidence = criterion.get("evidence", [])
        present_types = _evidence_types_present(evidence)
        missing = REQUIRED_EVIDENCE_TYPES - present_types

        if missing:
            failures.append(AuditFailure(
                criterion_id=cid,
                reason=f"missing required evidence types: {sorted(missing)}",
            ))
            continue

        audit = _find_audit_check(evidence)
        if audit and audit.get("satisfied") is False:
            failures.append(AuditFailure(
                criterion_id=cid,
                reason=f"audit_check.satisfied is false: {audit.get('rationale')}",
            ))

    return AuditResult(all_pass=(len(failures) == 0), audit_failures=failures)
