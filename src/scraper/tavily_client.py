import requests
from .config import ScraperConfig
from ._exceptions import ScraperError

class TavilyClient:
    """Simple wrapper for Tavily API"""
    ENDPOINT = "https://api.tavily.com/search"

    def __init__(self, cfg: ScraperConfig):
        self.api_key = cfg.tavily_api_key
        self.timeout = cfg.timeout

    def search(self, query: str, max_results: int = 20):
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
        }
        try:
            resp = requests.post(self.ENDPOINT, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            raise ScraperError(f"Tavily request failed: {exc}") from exc
