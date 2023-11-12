from typing import Any

import abc


class PageRetriever(abc.ABC):
    def retrieve_html(self, url: str, **kwargs: Any) -> str:
        raise NotImplementedError()
