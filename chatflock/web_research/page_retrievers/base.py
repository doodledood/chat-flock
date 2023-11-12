import abc


class PageRetriever(abc.ABC):
    def retrieve_html(self, url: str, **kwargs) -> str:
        raise NotImplementedError()
