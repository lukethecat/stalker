"""Authorized entrypoint: the only place probes should actually be launched from.

`crescendo.run_crescendo` itself has no notion of authorization -- it is
pure loop control and stays that way so it's testable/reusable without a
tape. This module is the hard gate: it refuses to run anything unless a
valid `redteam.target.registered` event already covers `target_id`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agent1_orchestrator.authorization import require_authorization
from agent1_orchestrator.budget import Budget
from agent1_orchestrator.crescendo import CrescendoResult, RoundResult
from agent1_orchestrator.crescendo import run_crescendo as _run_crescendo
from agent1_orchestrator.policies import AttackerPolicy, JudgePolicy, TargetClient


def run_authorized_crescendo(
    *,
    events: list[dict[str, Any]],
    target_id: str,
    probe_id: str,
    attacker: AttackerPolicy,
    judge: JudgePolicy,
    target: TargetClient,
    expected_behavior: str,
    rubric: dict[str, Any],
    budget: Budget,
    on_round: Callable[[RoundResult], None] | None = None,
) -> CrescendoResult:
    """Raises `authorization.NotAuthorized` and runs nothing if `target_id`
    has no unexpired `redteam.target.registered` event in `events`."""
    require_authorization(events, target_id)
    return _run_crescendo(
        probe_id=probe_id,
        attacker=attacker,
        judge=judge,
        target=target,
        expected_behavior=expected_behavior,
        rubric=rubric,
        budget=budget,
        on_round=on_round,
    )
