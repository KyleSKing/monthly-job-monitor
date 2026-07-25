"""Serper (serper.dev) search client — Tier 2 search engine."""

import os
import logging
import requests
from typing import List, Dict

logger = logging.getLogger(__name__)

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
            logger.warning("[Serper] No API key configured (set SERPER_API_KEY)")
            return []

        limit = limit or self.max_results
        payload = {"q": query, "num": limit, "gl": "cn", "hl": "zh-cn"}

        try:
            resp = self.session.post(SERPER_ENDPOINT, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("organic", [])
            logger.info(f"[Serper] query={query[:60]!r} → {len(results)} results")
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
        except requests.HTTPError as e:
            logger.warning(
                f"[Serper] HTTP {e.response.status_code} for query={query[:60]!r}: "
                f"{e.response.text[:200]}"
            )
            return []
        except Exception as e:
            logger.warning(f"[Serper] request failed for query={query[:60]!r}: {e}")
            return []
