"""Jina Reader client — Tier 1 content extraction.

Reads a URL and returns clean markdown via Jina's Reader API.
Usage: GET https://r.jina.ai/http://target-url
No API key needed for limited usage; set JINA_API_KEY for higher rate limits.
"""

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

JINA_API_KEY = os.getenv("JINA_API_KEY", "")
JINA_BASE = "https://r.jina.ai"


class JinaClient:
    """Fetch URL content as clean markdown via Jina Reader."""

    def __init__(self, api_key: str = "", timeout: int = 30):
        self.api_key = api_key or JINA_API_KEY
        self.timeout = timeout
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        self.session.headers.update(
            {
                "Accept": "text/markdown",
                "X-With-Generated-Alt": "true",
                "X-Return-Format": "markdown",
            }
        )

    def fetch(self, url: str) -> Optional[str]:
        """Fetch a URL and return clean markdown content. Silent on failure."""
        if not url or not url.strip():
            return None

        reader_url = f"{JINA_BASE}/{url.strip()}"
        try:
            resp = self.session.get(reader_url, timeout=8)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.warning(f"[Jina] fetch failed for {url}: {e}")
            return None

    def fetch_json(self, url: str) -> Optional[dict]:
        """Fetch a URL and return structured JSON (if Reader supports it)."""
        if not url or not url.strip():
            return None

        reader_url = f"{JINA_BASE}/{url.strip()}"
        try:
            resp = self.session.get(
                reader_url,
                headers={"Accept": "application/json"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[Jina] JSON fetch failed for {url}: {e}")
            return None
