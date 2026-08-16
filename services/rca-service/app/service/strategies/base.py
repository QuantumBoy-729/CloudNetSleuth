"""Base strategy contract for RCA analysis."""

from abc import ABC, abstractmethod

from app.models.rca import RCARequest, RCAResponse


class AnalysisStrategy(ABC):
    @abstractmethod
    def analyze(self, payload: RCARequest) -> RCAResponse:
        raise NotImplementedError

