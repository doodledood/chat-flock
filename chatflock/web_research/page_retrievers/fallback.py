from typing import Any, Sequence

from .base import PageRetriever


class RetrieverWithFallback(PageRetriever):
    def __init__(self, retrievers: Sequence[PageRetriever]):
        assert len(retrievers) > 0, 'Must provide at least one retriever.'

        self.retrievers = retrievers

    def retrieve_html(self, url: str, **kwargs: Any) -> str:
        last_error = None

        for retriever in self.retrievers:
            try:
                return retriever.retrieve_html(url, **kwargs)
            except Exception as e:
                last_error = e

        raise last_error or Exception('No retriever was able to retrieve the page.')
