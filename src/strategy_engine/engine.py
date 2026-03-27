"""Minimal strategy engine orchestration helper."""

from __future__ import annotations

from .contracts import StrategyEvaluation, StrategyInput
from .strategies.base import Strategy


class StrategyEngine:
    def evaluate(self, strategy: Strategy, strategy_input: StrategyInput) -> StrategyEvaluation:
        return strategy.evaluate(strategy_input)
