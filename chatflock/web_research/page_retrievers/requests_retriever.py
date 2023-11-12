import requests
from tenacity import retry, wait_random, wait_fixed, stop_after_attempt, retry_if_exception_type

from ..errors import TransientHTTPError, NonTransientHTTPError
from .base import PageRetriever


class SimpleRequestsPageRetriever(PageRetriever):
    @retry(retry=retry_if_exception_type(TransientHTTPError),
           wait=wait_fixed(2) + wait_random(0, 2),
           stop=stop_after_attempt(3))
    def retrieve_html(self, url: str, **kwargs) -> str:
        r = requests.get(url, **kwargs)
        if r.status_code < 300:
            return r.text

        if r.status_code >= 500:
            raise TransientHTTPError(r.status_code, r.text)

        raise NonTransientHTTPError(r.status_code, r.text)
