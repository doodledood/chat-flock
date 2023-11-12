import abc
import json
import os
from typing import List, Optional

import requests
from pydantic import BaseModel
from tenacity import retry, wait_fixed, wait_random, stop_after_attempt, retry_if_exception_type

from chatflock.web_research.errors import TransientHTTPError, NonTransientHTTPError


class OrganicSearchResult(BaseModel):
    position: int
    title: str
    link: str


class SearchResults(BaseModel):
    answer_snippet: Optional[str]
    knowledge_graph_description: Optional[str]
    organic_results: List[OrganicSearchResult]


class SearchResultsProvider(abc.ABC):
    @abc.abstractmethod
    def search(self, query: str, n_results: int = 3) -> SearchResults:
        raise NotImplementedError()


class GoogleSerperSearchResultsProvider(SearchResultsProvider):
    def __init__(self, api_key: Optional[str] = None):
        if api_key is None:
            api_key = os.environ['SERPER_API_KEY']

        self.api_key = api_key

    @retry(retry=retry_if_exception_type(TransientHTTPError),
           wait=wait_fixed(2) + wait_random(0, 2),
           stop=stop_after_attempt(3))
    def search(self, query: str, n_results: int = 3) -> SearchResults:
        assert 100 >= n_results > 0, 'n_results must be greater than 0 and less than or equal to 100'

        url = "https://google.serper.dev/search"

        payload = json.dumps({
            "q": query,
            "num": n_results + 5,  # Request extra results to account for non-organic results
        })
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

        r = requests.request("POST", url, headers=headers, data=payload)
        if r.status_code >= 300:
            if r.status_code >= 500:
                raise TransientHTTPError(r.status_code, r.text)

            raise NonTransientHTTPError(r.status_code, r.text)
        else:
            results = r.json()

            return SearchResults(
                answer_snippet=results.get('answerBox', {}).get('answer'),
                knowledge_graph_description=results.get('knowledgeGraph', {}).get('description'),
                organic_results=[
                    OrganicSearchResult(
                        position=organic_result['position'],
                        title=organic_result['title'],
                        link=organic_result['link']
                    ) for organic_result in results['organic'][:n_results]
                ]
            )
