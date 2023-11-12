from abc import ABC, abstractmethod
from typing import List, Optional


class CodeExecutor(ABC):
    @abstractmethod
    def execute(self, code: str, dependencies: Optional[List[str]] = None) -> str:
        pass
