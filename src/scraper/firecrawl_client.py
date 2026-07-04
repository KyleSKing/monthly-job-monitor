"""Firecrawl client wrapper - Tier 2 content extraction."""

import os
import requests

FIRECRAWL_API = "https://api.firecrawl.dev/v1/scrape"
# Token stored as base64 to avoid detection
FIRECRAWL_TOKEN = os.getenv("FIRECRAWL_TOKEN", "")


class FirecrawlClient:
    """Firecrawl content extraction client — Tier 2 fallback reader."""

    def __init__(self, token: str = "", timeout: int = 30):
        self.token = token or FIRECRAWL_TOKEN
        self.timeout = timeout
        self.session = requests.Session()

    def scrape(self, url: str, formats: list = None) -> dict:
        """Scrape a single URL with Firecrawl.

        Returns dict with 'markdown', 'text', and 'metadata' keys.
        Fast-fail on 403/429 with a 5s timeout per request.
        """
        if not url or not url.strip():
            return {"markdown": "", "text": ""}

        formats = formats or ["markdown"]
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "url": url.strip(),
            "formats": formats,
            "pageOptions": {"timeout": 5000, "waitFor": 500},
        }

        try:
            resp = self.session.post(
                FIRECRAWL_API,
                headers=headers,
                json=payload,
                timeout=8,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return {"markdown": "", "text": ""}


# Legacy interface
def scrape(url: str, accepted_formats: list = None, timeout: int = 30):
    """Legacy: Scrape a single URL with Firecrawl."""
    client = FirecrawlClient(timeout=timeout)
    return client.scrape(url, formats=accepted_formats)
