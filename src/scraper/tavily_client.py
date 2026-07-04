"""Tavily search client for job fetching and salary extraction."""

import json
import os
import re
import requests
from typing import List, Dict

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_ENDPOINT = "https://api.tavily.com/search"


class TavilyClient:
    """Tavily search client — Tier 3 fallback search engine."""

    def __init__(self, api_key: str = "", max_results: int = 10):
        self.api_key = api_key or TAVILY_API_KEY
        self.max_results = max_results
        self.session = requests.Session()

    def search(self, query: str, limit: int = 0) -> List[Dict]:
        """Search jobs via Tavily with content extraction."""
        limit = limit or self.max_results
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": limit,
            "include_answer": True,
            "search_depth": "advanced",
        }
        try:
            resp = self.session.post(TAVILY_ENDPOINT, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            answer = data.get("answer", "")
            for r in results:
                r["tavily_answer"] = answer
            return results
        except Exception:
            return []

    def fallback_fetch(self, target_url: str) -> List[str]:
        """Get candidate URLs via Tavily when primary fetch fails."""
        keywords = extract_keywords_from_url(target_url)
        raw_keywords = keywords.strip()
        if not raw_keywords:
            return []
        query = f"{raw_keywords} job Beijing"
        results = self.search(query, limit=3)
        urls = [
            r["url"]
            for r in results
            if "job" in r.get("url", "").lower() or "career" in r.get("url", "").lower()
        ]
        return urls[:2]


# --- Legacy functions kept for backward compatibility ---


def extract_keywords_from_url(url: str) -> str:
    """Extract keywords from a URL for search."""
    if "keywords=" not in url:
        return url.split("?")[0]
    raw = url.split("keywords=")[1]
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", raw)
    return cleaned


def search_jobs(query: str, max_results: int = 10) -> List[Dict]:
    """Search for jobs using Tavily API with content extraction."""
    client = TavilyClient()
    return client.search(query, limit=max_results)


def fallback_fetch(target_url: str) -> List[str]:
    """Get candidate URLs via Tavily when primary fetch fails."""
    client = TavilyClient()
    return client.fallback_fetch(target_url)
