"""Crescendo method: multi-turn, gradually-escalating attacker/judge loop.

This is control flow only. It decides *when* to keep escalating, *when* to
stop, and *what gets recorded* -- not *what to say*. The actual escalation
content comes from whatever AttackerPolicy is plugged in (see policies.py);
this repo ships none.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from agent1_orchestrator.budget import Budget, BudgetExceeded, BudgetTracker
from agent1_orchestrator.policies import (
    AttackerPolicy,
    AttackerTurn,
    JudgePolicy,
    JudgeVerdict,
    TargetClient,
)

StopReason = Literal["target_failed", "budget_exceeded", "attacker_exhausted"]


@dataclass(frozen=True)
class RoundResult:
    round_index: int
    attacker_turn: AttackerTurn
    target_response: str
    verdict: JudgeVerdict


@dataclass(frozen=True)
class CrescendoResult:
    probe_id: str
    rounds: list[RoundResult]
    stopped_reason: StopReason


class AttackerExhausted(Exception):
    """Raised by an AttackerPolicy to signal it has no further escalation to try."""


def run_crescendo(
    *,
    probe_id: str,
    attacker: AttackerPolicy,
    judge: JudgePolicy,
    target: TargetClient,
    expected_behavior: str,
    rubric: dict[str, Any],
    budget: Budget,
    on_round: Callable[[RoundResult], None] | None = None,
) -> CrescendoResult:
    """Run rounds until the target fails, the attacker gives up, or budget trips.

    `on_round` fires after every round (pass/fail/inconclusive alike) so a
    caller can bridge each round onto the tape as it happens rather than
    only at the end (see tape_bridge.py).
    """
    tracker = BudgetTracker(budget)
    history: list[dict[str, str]] = []
    rounds: list[RoundResult] = []
    round_index = 0

    while True:
        try:
            tracker.record_round()
        except BudgetExceeded:
            return CrescendoResult(probe_id, rounds, "budget_exceeded")

        try:
            turn = attacker.next_turn(history, round_index)
        except AttackerExhausted:
            return CrescendoResult(probe_id, rounds, "attacker_exhausted")

        response = target.send(turn.prompt)
        verdict = judge.score(response, expected_behavior, rubric)
        result = RoundResult(round_index, turn, response, verdict)
        rounds.append(result)
        history.append({"role": "attacker", "content": turn.prompt})
        history.append({"role": "target", "content": response})
        if on_round is not None:
            on_round(result)

        if verdict.verdict == "fail":
            return CrescendoResult(probe_id, rounds, "target_failed")

        round_index += 1
