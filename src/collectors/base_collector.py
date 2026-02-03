from abc import ABC, abstractmethod
from typing import List, Dict, Any

from config.loader import SourceConfig


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""

    def __init__(self, source: SourceConfig):
        self.source = source

    @abstractmethod
    def collect(self) -> List[Dict[str, Any]]:
        """Collect data from the configured source.

        Returns:
            List of dictionaries containing the raw collected data.
        """
        pass
