from abc import ABC, abstractmethod
from typing import Optional, Sequence


class CodeExecutor(ABC):
    @abstractmethod
    def execute(self, code: str, dependencies: Optional[Sequence[str]] = None) -> str:
        pass
