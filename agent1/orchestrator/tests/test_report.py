import pytest
from agent1_orchestrator.crescendo import CrescendoResult, RoundResult
from agent1_orchestrator.policies import AttackerTurn, JudgeVerdict
from agent1_orchestrator.report import (
    build_report,
    finding_from_crescendo_result,
    group_by_owasp,
    render_markdown,
)

FINDINGS = [
    {
        "finding_id": "f-low",
        "category": {"owasp": "LLM01"},
        "affected_component": "chat",
        "reproducible_case_ref": "r1",
        "severity": "low",
    },
    {
        "finding_id": "f-crit",
        "category": {"owasp": "LLM01"},
        "affected_component": "chat",
        "reproducible_case_ref": "r2",
        "severity": "critical",
        "remediation_hint": "patch it",
    },
    {
        "finding_id": "f-med",
        "category": {"owasp": "LLM06"},
        "affected_component": "rag",
        "reproducible_case_ref": "r3",
        "severity": "medium",
    },
]


class TestBuildReport:
    def test_orders_by_severity(self):
        report = build_report(report_id="r-1", findings=FINDINGS)
        assert [f["finding_id"] for f in report.findings] == ["f-crit", "f-med", "f-low"]

    def test_summary_counts(self):
        report = build_report(report_id="r-1", findings=FINDINGS)
        assert "1 critical" in report.summary
        assert "1 medium" in report.summary
        assert "1 low" in report.summary

    def test_empty_findings(self):
        report = build_report(report_id="r-empty", findings=[])
        assert report.summary == "0 findings"
        assert report.finding_refs() == []

    def test_to_event_payload_matches_c2_shape(self):
        report = build_report(report_id="r-1", findings=FINDINGS)
        payload = report.to_event_payload()
        assert payload["report_id"] == "r-1"
        assert set(payload["finding_refs"]) == {"f-low", "f-crit", "f-med"}


class TestGroupByOwasp:
    def test_groups_correctly(self):
        groups = group_by_owasp(FINDINGS)
        assert {f["finding_id"] for f in groups["LLM01"]} == {"f-low", "f-crit"}
        assert {f["finding_id"] for f in groups["LLM06"]} == {"f-med"}

    def test_unmapped_category(self):
        groups = group_by_owasp([{"finding_id": "f-x", "category": {}, "severity": "low"}])
        assert {f["finding_id"] for f in groups["unmapped"]} == {"f-x"}


def make_round(index: int, verdict: str) -> RoundResult:
    return RoundResult(
        round_index=index,
        attacker_turn=AttackerTurn(prompt=f"test-{index}", vector="test-vector"),
        target_response="response",
        verdict=JudgeVerdict(verdict, 0.0, "because"),
    )


class TestFindingFromCrescendoResult:
    def test_builds_finding_from_target_failed_result(self):
        result = CrescendoResult(probe_id="probe-1", rounds=[make_round(0, "pass"), make_round(1, "fail")], stopped_reason="target_failed")
        finding = finding_from_crescendo_result(
            finding_id="f-1",
            result=result,
            category={"owasp": "LLM01"},
            affected_component="chat",
            severity="high",
            remediation_hint="patch it",
        )
        assert finding["finding_id"] == "f-1"
        assert finding["reproducible_case_ref"] == "probe-1#round-1"
        assert finding["remediation_hint"] == "patch it"

    def test_omits_remediation_hint_when_none(self):
        result = CrescendoResult(probe_id="probe-1", rounds=[make_round(0, "fail")], stopped_reason="target_failed")
        finding = finding_from_crescendo_result(
            finding_id="f-1", result=result, category={}, affected_component="chat", severity="low"
        )
        assert "remediation_hint" not in finding

    def test_raises_for_non_failed_result(self):
        result = CrescendoResult(probe_id="probe-1", rounds=[make_round(0, "pass")], stopped_reason="budget_exceeded")
        with pytest.raises(ValueError):
            finding_from_crescendo_result(
                finding_id="f-1", result=result, category={}, affected_component="chat", severity="low"
            )


class TestRenderMarkdown:
    def test_contains_finding_ids_and_severity(self):
        report = build_report(report_id="r-1", findings=FINDINGS)
        md = render_markdown(report)
        assert "f-crit" in md
        assert "CRITICAL" in md
        assert "patch it" in md
        assert "(none recorded)" in md
