"""Toy attacker/judge/target for demonstrating the orchestrator end-to-end.

This is a mechanism demo, not a red-team methodology. The "target" is a toy
state machine that stays LOCKED for a fixed number of attempts and then
flips to UNLOCKED -- it has zero resemblance to any real harm category or
escalation tactic. It exists so the Crescendo loop, authorization gate,
tape bridge, and report generator can all be exercised together without any
real attacker/judge content, which stays private per CLAUDE.md house rule 4
("空弹匣" -- this repo ships method, never payload).

Do not mistake this for a reference implementation of an actual red-team
policy. Wire in a real (private) AttackerPolicy/JudgePolicy instead.
"""

from __future__ import annotations

from agent1_orchestrator.crescendo import AttackerExhausted
from agent1_orchestrator.policies import AttackerTurn, JudgeVerdict


class ToyAttacker:
    """Cycles through numbered no-op prompts up to `max_attempts`."""

    def __init__(self, max_attempts: int = 5):
        self._max_attempts = max_attempts

    def next_turn(self, history: list[dict[str, str]], round_index: int) -> AttackerTurn:
        if round_index >= self._max_attempts:
            raise AttackerExhausted
        return AttackerTurn(prompt=f"attempt #{round_index}", vector="toy-persistence")


class ToyJudge:
    """fail iff the toy target's state flipped to UNLOCKED."""

    def score(self, target_response: str, expected_behavior: str, rubric: dict) -> JudgeVerdict:
        if target_response == "UNLOCKED":
            return JudgeVerdict("fail", 1.0, "toy target flipped to UNLOCKED")
        return JudgeVerdict("pass", 0.0, "toy target still LOCKED")


class ToyTarget:
    """Deterministic state machine: LOCKED until `flips_after` attempts,
    then UNLOCKED forever. Simulates "the target eventually gives in" with
    no actual content involved -- there is nothing to jailbreak here."""

    def __init__(self, flips_after: int = 3):
        self._flips_after = flips_after
        self._attempts = 0

    def send(self, prompt: str) -> str:
        self._attempts += 1
        return "UNLOCKED" if self._attempts >= self._flips_after else "LOCKED"
