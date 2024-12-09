from typing import Dict, List
from urllib.parse import urlencode

import requests


class NaverOpenAPIClient:
    """
    https://developers.naver.com/docs/serviceapi/search/news/news.md#%EB%89%B4%EC%8A%A4

    client = NaverOpenAPIClient(
        client_id=os.getenv("NAVER_OPEN_API_CLIENT_ID"),
        client_secret=os.getenv("NAVER_OPEN_API_CLIENT_SECRET"),
    )
    news_urls = client.get_news_urls(
        query="계엄령",
        display=10,
    )
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        api_url: str = "https://openapi.naver.com",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = api_url

    @property
    def header(self) -> Dict[str, str]:
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

    def http_get(self, url: str) -> Dict:
        response = requests.get(url, headers=self.header)
        response.raise_for_status()
        return response.json()

    def request_news(
        self,
        query: str,
        display: int,
        start: int,
        sort: str,
    ) -> Dict:
        assert query != ""
        assert 10 <= display <= 100
        assert 1 <= start <= 100
        assert sort in ["sim", "date"]

        params = urlencode({"query": query, "display": display, "start": start, "sort": sort})
        url = f"{self.api_url}/v1/search/news.json?{params}"
        return self.http_get(url)

    def get_news_urls(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "date",
    ) -> List[str]:
        news_items = self.request_news(query, display, start, sort)
        return [item["link"] for item in news_items["items"]]
