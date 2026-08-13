"""Budget circuit breaker for the attack loop.

Every round costs queries and (usually) money against a real target and a
real model provider; an agentic loop that decides its own next vector at
runtime needs a hard stop that isn't "the attacker gave up."
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Budget:
    max_rounds: int = 5
    max_cost_usd: float | None = None
    max_seconds: float | None = None


class BudgetExceeded(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class BudgetTracker:
    """Mutable counter checked once per round; raises BudgetExceeded on trip."""

    def __init__(self, budget: Budget):
        self.budget = budget
        self.rounds = 0
        self.cost_usd = 0.0
        self._started_at = time.monotonic()

    def record_round(self, cost_usd: float = 0.0) -> None:
        self.rounds += 1
        self.cost_usd += cost_usd
        self._check()

    def elapsed_seconds(self) -> float:
        return time.monotonic() - self._started_at

    def _check(self) -> None:
        if self.rounds > self.budget.max_rounds:
            raise BudgetExceeded(f"max_rounds exceeded ({self.rounds} > {self.budget.max_rounds})")
        if self.budget.max_cost_usd is not None and self.cost_usd > self.budget.max_cost_usd:
            raise BudgetExceeded(f"max_cost_usd exceeded ({self.cost_usd} > {self.budget.max_cost_usd})")
        if self.budget.max_seconds is not None and self.elapsed_seconds() > self.budget.max_seconds:
            raise BudgetExceeded(f"max_seconds exceeded ({self.elapsed_seconds():.1f} > {self.budget.max_seconds})")
