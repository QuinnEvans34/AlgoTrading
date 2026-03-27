"""Strategy interface contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..contracts import StrategyEvaluation, StrategyInput


class Strategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Stable strategy identifier."""

    @abstractmethod
    def evaluate(self, strategy_input: StrategyInput) -> StrategyEvaluation:
        """Evaluate a strategy against normalized candles."""
