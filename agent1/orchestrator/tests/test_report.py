from agent1_orchestrator.report import build_report, group_by_owasp, render_markdown

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


class TestRenderMarkdown:
    def test_contains_finding_ids_and_severity(self):
        report = build_report(report_id="r-1", findings=FINDINGS)
        md = render_markdown(report)
        assert "f-crit" in md
        assert "CRITICAL" in md
        assert "patch it" in md
        assert "(none recorded)" in md
