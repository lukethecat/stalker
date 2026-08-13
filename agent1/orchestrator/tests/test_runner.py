import pytest
from agent1_orchestrator.authorization import NotAuthorized
from agent1_orchestrator.budget import Budget
from agent1_orchestrator.crescendo import AttackerExhausted
from agent1_orchestrator.policies import AttackerTurn, JudgeVerdict
from agent1_orchestrator.runner import run_authorized_crescendo


class OneShotAttacker:
    def next_turn(self, history, round_index):
        if round_index > 0:
            raise AttackerExhausted
        return AttackerTurn(prompt="test", vector="test")


class AlwaysFailJudge:
    def score(self, target_response, expected_behavior, rubric):
        return JudgeVerdict("fail", 0.0, "stub")


class EchoTarget:
    def send(self, prompt):
        return "response"


def registration_event(target_id):
    return {
        "event": "redteam.target.registered",
        "payload": {"target": {"id": target_id}, "authorization": {"scope": ["POST /x"], "authorized_by": "a"}},
    }


class TestRunAuthorizedCrescendo:
    def test_raises_without_authorization(self):
        with pytest.raises(NotAuthorized):
            run_authorized_crescendo(
                events=[],
                target_id="t1",
                probe_id="p1",
                attacker=OneShotAttacker(),
                judge=AlwaysFailJudge(),
                target=EchoTarget(),
                expected_behavior="...",
                rubric={},
                budget=Budget(max_rounds=5),
            )

    def test_runs_when_authorized(self):
        result = run_authorized_crescendo(
            events=[registration_event("t1")],
            target_id="t1",
            probe_id="p1",
            attacker=OneShotAttacker(),
            judge=AlwaysFailJudge(),
            target=EchoTarget(),
            expected_behavior="...",
            rubric={},
            budget=Budget(max_rounds=5),
        )
        assert result.stopped_reason == "target_failed"
        assert len(result.rounds) == 1

    def test_does_not_run_attacker_when_unauthorized(self):
        calls = []

        class SpyAttacker:
            def next_turn(self, history, round_index):
                calls.append(round_index)
                raise AttackerExhausted

        with pytest.raises(NotAuthorized):
            run_authorized_crescendo(
                events=[],
                target_id="t1",
                probe_id="p1",
                attacker=SpyAttacker(),
                judge=AlwaysFailJudge(),
                target=EchoTarget(),
                expected_behavior="...",
                rubric={},
                budget=Budget(max_rounds=5),
            )
        assert calls == []
