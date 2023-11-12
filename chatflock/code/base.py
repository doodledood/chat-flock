from typing import Optional, Sequence

from abc import ABC, abstractmethod


class CodeExecutor(ABC):
    @abstractmethod
    def execute(self, code: str, dependencies: Optional[Sequence[str]] = None) -> str:
        pass
