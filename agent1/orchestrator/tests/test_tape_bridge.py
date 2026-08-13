import pytest

pytest.importorskip("bub", reason="tape_bridge integration needs the real bub package (Python >=3.12, see agent0/dispatcher/README.md)")

from agent1_orchestrator.crescendo import RoundResult
from agent1_orchestrator.policies import AttackerTurn, JudgeVerdict
from agent1_orchestrator.tape_bridge import (
    append_event_to_tape,
    finding_to_event,
    round_to_event,
)
from bub.tape import InMemoryTapeStore


def make_round(index: int, verdict: str) -> RoundResult:
    return RoundResult(
        round_index=index,
        attacker_turn=AttackerTurn(prompt=f"test-{index}", vector="test-vector"),
        target_response="response",
        verdict=JudgeVerdict(verdict, 0.5, "because"),
    )


class TestRoundToEvent:
    def test_shape_is_schema_valid(self):
        event = round_to_event(probe_id="probe-1", result=make_round(0, "pass"), run_id="run-1")
        assert event["event"] == "redteam.attack.round.completed"
        assert event["payload"]["probe_ref"] == "probe-1"
        assert event["payload"]["verdict"] == "pass"


class TestFindingToEvent:
    def test_shape_is_schema_valid(self):
        finding = {
            "finding_id": "f-1",
            "category": {"owasp": "LLM01"},
            "affected_component": "chat",
            "reproducible_case_ref": "run-1#seq-1",
            "severity": "high",
        }
        event = finding_to_event(finding=finding, run_id="run-1")
        assert event["event"] == "redteam.finding.logged"
        assert event["payload"] == finding


class TestAppendEventToTape:
    def test_appends_as_tape_event_entry(self):
        store = InMemoryTapeStore()
        event = round_to_event(probe_id="probe-1", result=make_round(0, "pass"), run_id="run-1")
        append_event_to_tape(store, "main", event)

        entries = store.read("main")
        assert len(entries) == 1
        assert entries[0].kind == "event"
        assert entries[0].payload["name"] == "redteam.attack.round.completed"
        assert entries[0].payload["data"] == event["payload"]
        assert entries[0].meta["c2_run_id"] == "run-1"

    def test_dispatcher_can_read_it_back(self):
        """Cross-check against agent0-ipo-dispatcher's own matching logic."""
        import sys
        from pathlib import Path

        dispatcher_src = Path(__file__).resolve().parents[3] / "agent0" / "dispatcher" / "src"
        sys.path.insert(0, str(dispatcher_src))
        try:
            from agent0_ipo_dispatcher.plugin import matches_any
        finally:
            sys.path.remove(str(dispatcher_src))

        store = InMemoryTapeStore()
        event = round_to_event(probe_id="probe-1", result=make_round(0, "fail"), run_id="run-1")
        append_event_to_tape(store, "main", event)

        entry = store.read("main")[0]
        assert matches_any(entry.payload["name"], {"redteam.*"})
