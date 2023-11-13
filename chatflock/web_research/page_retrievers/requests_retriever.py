from typing import Any

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed, wait_random

from ..errors import NonTransientHTTPError, TransientHTTPError
from .base import PageRetriever


class SimpleRequestsPageRetriever(PageRetriever):
    default_timeout: int = 10

    @retry(
        retry=retry_if_exception_type(TransientHTTPError),
        wait=wait_fixed(2) + wait_random(0, 2),
        stop=stop_after_attempt(3),
    )
    def retrieve_html(self, url: str, **kwargs: Any) -> str:
        default_kwargs = {"timeout": self.default_timeout}

        r = requests.get(
            url, **{**default_kwargs, **kwargs}
        )  # nosec - Dealt with timeouts already in the previous line
        if r.status_code < 300:
            return r.text

        if r.status_code >= 500:
            raise TransientHTTPError(r.status_code, r.text)

        raise NonTransientHTTPError(r.status_code, r.text)
