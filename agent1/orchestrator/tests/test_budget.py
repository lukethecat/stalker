import time

import pytest
from agent1_orchestrator.budget import Budget, BudgetExceeded, BudgetTracker


class TestBudgetTracker:
    def test_within_max_rounds_ok(self):
        tracker = BudgetTracker(Budget(max_rounds=3))
        for _ in range(3):
            tracker.record_round()
        assert tracker.rounds == 3

    def test_exceeds_max_rounds(self):
        tracker = BudgetTracker(Budget(max_rounds=2))
        tracker.record_round()
        tracker.record_round()
        with pytest.raises(BudgetExceeded):
            tracker.record_round()

    def test_exceeds_max_cost(self):
        tracker = BudgetTracker(Budget(max_rounds=100, max_cost_usd=1.0))
        tracker.record_round(cost_usd=0.6)
        with pytest.raises(BudgetExceeded):
            tracker.record_round(cost_usd=0.6)

    def test_exceeds_max_seconds(self):
        tracker = BudgetTracker(Budget(max_rounds=100, max_seconds=0.01))
        tracker.record_round()
        time.sleep(0.02)
        with pytest.raises(BudgetExceeded):
            tracker.record_round()

    def test_no_limits_never_trips(self):
        tracker = BudgetTracker(Budget(max_rounds=1_000_000))
        for _ in range(50):
            tracker.record_round(cost_usd=1000.0)
