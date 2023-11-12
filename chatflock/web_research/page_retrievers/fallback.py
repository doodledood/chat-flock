from typing import List

from chatflock.web_research.page_retrievers import PageRetriever


class RetrieverWithFallback(PageRetriever):
    def __init__(self, retrievers: List[PageRetriever]):
        assert len(retrievers) > 0, 'Must provide at least one retriever.'

        self.retrievers = retrievers

    def retrieve_html(self, url: str, **kwargs) -> str:
        last_error = None
        for retriever in self.retrievers:
            try:
                return retriever.retrieve_html(url, **kwargs)
            except Exception as e:
                last_error = e

        if last_error is not None:
            raise last_error
