"""Serper (serper.dev) search client — Tier 2 search engine."""

import os
import requests
from typing import List, Dict

SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
SERPER_ENDPOINT = "https://google.serper.dev/search"


class SerperClient:
    """Google search via Serper API. Returns organic results with snippets."""

    def __init__(self, api_key: str = "", max_results: int = 10):
        self.api_key = api_key or SERPER_API_KEY
        self.max_results = max_results
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json",
            }
        )

    def search(self, query: str, limit: int = 0) -> List[Dict]:
        """Search via Serper Google Search API.

        Returns list of dicts with: url, title, snippet, position
        """
        if not self.api_key:
            print("[Serper] No API key configured (set SERPER_API_KEY)")
            return []

        limit = limit or self.max_results
        payload = {"q": query, "num": limit, "gl": "cn", "hl": "zh-cn"}

        try:
            resp = self.session.post(SERPER_ENDPOINT, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("organic", [])
            out = []
            for r in results[:limit]:
                out.append(
                    {
                        "url": r.get("link", ""),
                        "title": r.get("title", ""),
                        "snippet": r.get("snippet", ""),
                        "position": r.get("position", 0),
                    }
                )
            return out
        except Exception as e:
            print(f"[Serper] Search failed for '{query}': {e}")
            return []
