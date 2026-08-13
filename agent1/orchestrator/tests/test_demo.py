"""Exercises examples/demo_run.py directly (not via subprocess) so the toy
end-to-end pipeline is checked on every test run, not just eyeballed."""

import sys
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def demo_run():
    sys.path.insert(0, str(EXAMPLES_DIR))
    try:
        import demo_run as module

        yield module
    finally:
        sys.path.remove(str(EXAMPLES_DIR))
        sys.modules.pop("demo_run", None)
        sys.modules.pop("toy_policies", None)


class TestRunDemo:
    def test_toy_target_eventually_fails(self, demo_run):
        result, _report, _tape_entry_count = demo_run.run_demo()
        assert result.stopped_reason == "target_failed"
        assert len(result.rounds) == 3
        assert [r.verdict.verdict for r in result.rounds] == ["pass", "pass", "fail"]

    def test_produces_exactly_one_finding(self, demo_run):
        _result, report, _tape_entry_count = demo_run.run_demo()
        assert len(report.findings) == 1
        assert report.findings[0]["finding_id"] == "toy-finding-1"

    def test_report_renders_without_error(self, demo_run):
        from agent1_orchestrator.report import render_markdown

        _result, report, _tape_entry_count = demo_run.run_demo()
        md = render_markdown(report)
        assert "toy-finding-1" in md


class TestRunDemoWithBub:
    def test_tape_entry_count_when_bub_available(self, demo_run):
        pytest.importorskip("bub", reason="needs the real bub package (Python >=3.12 uv venv)")
        _result, _report, tape_entry_count = demo_run.run_demo()
        # 1 registration + 3 rounds + 1 finding
        assert tape_entry_count == 5
