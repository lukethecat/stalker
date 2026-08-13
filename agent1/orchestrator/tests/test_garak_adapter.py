import sys
from pathlib import Path

from agent1_orchestrator.garak_adapter import GarakRunConfig, run_garak

FAKE_GARAK_SCRIPT = """
import json, sys
report_path = sys.argv[1]
with open(report_path, "w") as f:
    f.write(json.dumps({"probe": "demo.Probe", "detector": "demo.Detector", "passed": False}) + "\\n")
    f.write(json.dumps({"probe": "demo.Probe2", "detector": "demo.Detector", "passed": True}) + "\\n")
    f.write(json.dumps({"not_a_finding_row": True}) + "\\n")
print("done")
"""


class TestRunGarak:
    def test_parses_jsonl_report_with_default_filter(self, tmp_path: Path):
        script = tmp_path / "fake_garak.py"
        script.write_text(FAKE_GARAK_SCRIPT)
        report_path = tmp_path / "report.jsonl"

        result = run_garak(
            GarakRunConfig(
                argv=[sys.executable, str(script), str(report_path)],
                report_jsonl=report_path,
            )
        )

        assert result.returncode == 0
        assert not result.timed_out
        assert "done" in result.stdout
        assert len(result.rows) == 2  # the non-finding row is filtered out by default
        assert {row["probe"] for row in result.rows} == {"demo.Probe", "demo.Probe2"}

    def test_missing_report_file_returns_empty_rows(self, tmp_path: Path):
        result = run_garak(
            GarakRunConfig(
                argv=[sys.executable, "-c", "print('no report written')"],
                report_jsonl=tmp_path / "does-not-exist.jsonl",
            )
        )
        assert result.returncode == 0
        assert result.rows == []

    def test_custom_row_filter(self, tmp_path: Path):
        script = tmp_path / "fake_garak.py"
        script.write_text(FAKE_GARAK_SCRIPT)
        report_path = tmp_path / "report.jsonl"

        result = run_garak(
            GarakRunConfig(
                argv=[sys.executable, str(script), str(report_path)],
                report_jsonl=report_path,
                row_filter=lambda row: row.get("passed") is False,
            )
        )
        assert len(result.rows) == 1
        assert result.rows[0]["probe"] == "demo.Probe"

    def test_nonzero_exit_is_not_raised(self, tmp_path: Path):
        result = run_garak(
            GarakRunConfig(
                argv=[sys.executable, "-c", "import sys; sys.exit(3)"],
                report_jsonl=tmp_path / "report.jsonl",
            )
        )
        assert result.returncode == 3
        assert result.rows == []

    def test_timeout_is_reported_not_raised(self, tmp_path: Path):
        result = run_garak(
            GarakRunConfig(
                argv=[sys.executable, "-c", "import time; time.sleep(5)"],
                report_jsonl=tmp_path / "report.jsonl",
                timeout_seconds=0.2,
            )
        )
        assert result.timed_out
        assert result.rows == []
