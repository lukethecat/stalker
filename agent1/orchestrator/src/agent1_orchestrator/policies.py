"""Pluggable interfaces for the attack loop.

This module defines *shapes only* -- no attacker or judge prompt content
lives in this repo (house rule: "空弹匣" / empty magazine, see CLAUDE.md).
Real Crescendo/GOAT/TAP prompting strategies and rubrics are private skills
supplied at runtime by whoever has authorization to run them; this repo only
needs to agree on the Protocol they implement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

Verdict = Literal["pass", "fail", "inconclusive"]


@dataclass(frozen=True)
class AttackerTurn:
    """One attacker-LLM output for a single round."""

    prompt: str
    vector: str  # short tag for the tactic used this round, e.g. "role-play-escalation"


@dataclass(frozen=True)
class JudgeVerdict:
    """One judge-LLM scoring of a single round.

    `verdict` follows the C2 `redteam.attack.round.completed` payload contract
    (spec/schema/c2_events.schema.json): "pass" means the target resisted as
    expected, "fail" means the target was compromised on this round, and
    "inconclusive" means keep escalating without a confident read yet.
    """

    verdict: Verdict
    score: float
    rationale: str


class AttackerPolicy(Protocol):
    """Produces the next attacker turn given prior round history."""

    def next_turn(self, history: list[dict[str, str]], round_index: int) -> AttackerTurn: ...


class JudgePolicy(Protocol):
    """Scores one target response against an expected behavior + rubric."""

    def score(self, target_response: str, expected_behavior: str, rubric: dict[str, Any]) -> JudgeVerdict: ...


class TargetClient(Protocol):
    """Sends one prompt to the authorized target and returns its response."""

    def send(self, prompt: str) -> str: ...
