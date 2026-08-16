"""Repository for strategy wiring."""

from app.service.strategies.base import AnalysisStrategy
from app.service.strategies.pearson import PearsonCorrelationStrategy


class StrategyRepository:
    def get_default_strategy(self) -> AnalysisStrategy:
        return PearsonCorrelationStrategy()

