import abc
from typing import Any


class PageRetriever(abc.ABC):
    def retrieve_html(self, url: str, **kwargs: Any) -> str:
        raise NotImplementedError()
