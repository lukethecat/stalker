"""Aggregate logged findings into a purple-team report.

Per docs/architecture.md, every finding carries four elements: category
(OWASP/ATLAS/NIST) + affected component + reproducible case + remediation
path. This module only aggregates and renders findings that already have
that shape (spec/schema/c2_events.schema.json's `redteam.finding.logged`
payload) -- it does not decide what counts as a finding.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SEVERITY_DISPLAY_ORDER = ("critical", "high", "medium", "low")


@dataclass(frozen=True)
class Report:
    report_id: str
    summary: str
    findings: list[dict[str, Any]]

    def finding_refs(self) -> list[str]:
        return [f["finding_id"] for f in self.findings]

    def to_event_payload(self) -> dict[str, Any]:
        """Shape matching the `redteam.report.ready` C2 event payload."""
        return {"report_id": self.report_id, "finding_refs": self.finding_refs(), "summary": self.summary}


def build_report(*, report_id: str, findings: list[dict[str, Any]]) -> Report:
    ordered = sorted(findings, key=lambda f: SEVERITY_ORDER.get(f.get("severity", ""), len(SEVERITY_ORDER)))
    counts = Counter(f.get("severity", "unknown") for f in findings)
    parts = [f"{counts[s]} {s}" for s in SEVERITY_DISPLAY_ORDER if counts.get(s)]
    summary = f"{len(findings)} finding(s): " + ", ".join(parts) if findings else "0 findings"
    return Report(report_id=report_id, summary=summary, findings=ordered)


def group_by_owasp(findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for finding in findings:
        key = (finding.get("category") or {}).get("owasp") or "unmapped"
        groups[key].append(finding)
    return dict(groups)


def render_markdown(report: Report) -> str:
    lines = [f"# Red Team Report `{report.report_id}`", "", report.summary, ""]
    for finding in report.findings:
        category = finding.get("category") or {}
        category_str = " / ".join(f"{k.upper()}:{v}" for k, v in category.items() if v) or "unmapped"
        lines += [
            f"## {finding['finding_id']} — {finding.get('severity', 'unknown').upper()}",
            f"- **Category:** {category_str}",
            f"- **Affected component:** {finding.get('affected_component', '?')}",
            f"- **Reproducible case:** {finding.get('reproducible_case_ref', '?')}",
            f"- **Remediation:** {finding.get('remediation_hint') or '(none recorded)'}",
            "",
        ]
    return "\n".join(lines)
