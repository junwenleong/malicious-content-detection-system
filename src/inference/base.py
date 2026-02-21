from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Any, Dict


class BasePredictor(ABC):
    """Abstract base class for all predictors."""

    config: Dict[str, Any]

    @abstractmethod
    def predict(
        self, texts: List[str], threshold: Optional[float] = None
    ) -> Tuple[List[str], List[float], float]:
        """Synchronous prediction."""
        pass

    @abstractmethod
    async def apredict(
        self, texts: List[str], threshold: Optional[float] = None
    ) -> Tuple[List[str], List[float], float]:
        """Asynchronous prediction."""
        pass
