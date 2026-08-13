"""Loop-mechanics tests only. Attacker/target/judge below are deterministic,
content-free stubs -- no real escalation or jailbreak text anywhere here."""

from agent1_orchestrator.budget import Budget
from agent1_orchestrator.crescendo import AttackerExhausted, run_crescendo
from agent1_orchestrator.policies import AttackerTurn, JudgeVerdict


class ScriptedAttacker:
    def __init__(self, turns: list[AttackerTurn]):
        self._turns = turns

    def next_turn(self, history, round_index):
        if round_index >= len(self._turns):
            raise AttackerExhausted
        return self._turns[round_index]


class ScriptedTarget:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)

    def send(self, prompt):
        return self._responses.pop(0)


class KeywordJudge:
    """fail == response is missing the REFUSED marker. Purely mechanical stub."""

    def score(self, target_response, expected_behavior, rubric):
        if "REFUSED" in target_response:
            return JudgeVerdict("pass", 1.0, "target refused")
        return JudgeVerdict("fail", 0.0, "target did not refuse")


def turn(i: int) -> AttackerTurn:
    return AttackerTurn(prompt=f"test-prompt-{i}", vector="test-vector")


class TestRunCrescendo:
    def test_stops_on_target_failed(self):
        attacker = ScriptedAttacker([turn(0), turn(1), turn(2)])
        target = ScriptedTarget(["REFUSED: no.", "REFUSED: still no.", "sure, here you go"])
        result = run_crescendo(
            probe_id="probe-1",
            attacker=attacker,
            judge=KeywordJudge(),
            target=target,
            expected_behavior="target should keep refusing",
            rubric={},
            budget=Budget(max_rounds=10),
        )
        assert result.stopped_reason == "target_failed"
        assert len(result.rounds) == 3
        assert [r.verdict.verdict for r in result.rounds] == ["pass", "pass", "fail"]

    def test_stops_on_budget_exceeded(self):
        attacker = ScriptedAttacker([turn(i) for i in range(10)])
        target = ScriptedTarget(["REFUSED"] * 10)
        result = run_crescendo(
            probe_id="probe-2",
            attacker=attacker,
            judge=KeywordJudge(),
            target=target,
            expected_behavior="...",
            rubric={},
            budget=Budget(max_rounds=3),
        )
        assert result.stopped_reason == "budget_exceeded"
        assert len(result.rounds) == 3

    def test_stops_on_attacker_exhausted(self):
        attacker = ScriptedAttacker([turn(0)])
        target = ScriptedTarget(["REFUSED"])
        result = run_crescendo(
            probe_id="probe-3",
            attacker=attacker,
            judge=KeywordJudge(),
            target=target,
            expected_behavior="...",
            rubric={},
            budget=Budget(max_rounds=10),
        )
        assert result.stopped_reason == "attacker_exhausted"
        assert len(result.rounds) == 1

    def test_on_round_callback_fires_each_round(self):
        attacker = ScriptedAttacker([turn(0), turn(1)])
        target = ScriptedTarget(["REFUSED", "give up"])
        seen = []
        run_crescendo(
            probe_id="probe-4",
            attacker=attacker,
            judge=KeywordJudge(),
            target=target,
            expected_behavior="...",
            rubric={},
            budget=Budget(max_rounds=10),
            on_round=seen.append,
        )
        assert len(seen) == 2
        assert seen[-1].verdict.verdict == "fail"

    def test_probe_id_carried_through(self):
        attacker = ScriptedAttacker([turn(0)])
        target = ScriptedTarget(["give up"])
        result = run_crescendo(
            probe_id="probe-xyz",
            attacker=attacker,
            judge=KeywordJudge(),
            target=target,
            expected_behavior="...",
            rubric={},
            budget=Budget(max_rounds=10),
        )
        assert result.probe_id == "probe-xyz"
