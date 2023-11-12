from typing import Any, Dict, Optional

import os

from .requests_retriever import SimpleRequestsPageRetriever


class ScraperAPIPageRetriever(SimpleRequestsPageRetriever):
    def __init__(self, api_key: Optional[str] = None, render_js: bool = False):
        super().__init__()

        if api_key is None:
            if "SCRAPERAPI_API_KEY" not in os.environ:
                raise ValueError("SCRAPERAPI_API_KEY environment variable is required or api_key argument.")

            api_key = os.environ["SCRAPERAPI_API_KEY"]

        self.api_key = api_key
        self.render_js = render_js

    def retrieve_html(self, url: str, **kwargs: Any) -> str:
        return super().retrieve_html(url, params={"api_key": self.api_key, "url": url, "render": self.render_js})
