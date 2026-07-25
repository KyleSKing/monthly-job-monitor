"""Exa (exa.ai) search client — Tier 1 primary search engine."""

import os
import re
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

EXA_API_KEY = os.getenv("EXA_API_KEY", "")
EXA_ENDPOINT = "https://api.exa.ai/search"


class ExaClient:
    """Semantic search via Exa API. Returns relevant URLs with summaries."""

    def __init__(self, api_key: str = "", max_results: int = 10):
        self.api_key = api_key or EXA_API_KEY
        self.max_results = max_results
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def search(self, query: str, site: str = "", limit: int = 0) -> List[Dict]:
        """Search Exa for job listings.

        Args:
            query: Search keywords
            site: Optional site filter (e.g. 'linkedin.com', 'zhaopin.com')
            limit: Max results (defaults to self.max_results)

        Returns:
            List of dicts with keys: url, title, text (snippet)
        """
        if not self.api_key:
            logger.warning("[Exa] No API key configured (set EXA_API_KEY)")
            return []

        limit = limit or self.max_results

        # Exa does not understand Google-style `site:domain` operators; extract
        # any such tokens from the query and pass them as includeDomains instead.
        domains = re.findall(r"site:(\S+)", query)
        clean_query = re.sub(r"site:\S+\s*", "", query).strip()
        include_domains = [d.split("/")[0] for d in domains] or ([site] if site else [])

        payload = {
            "query": clean_query or query,
            "numResults": limit,
            "contents": {"text": True, "summary": True},
        }
        if include_domains:
            payload["includeDomains"] = include_domains

        try:
            resp = self.session.post(EXA_ENDPOINT, json=payload, timeout=25)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", data.get("data", []))
            logger.info(
                f"[Exa] query={clean_query[:60]!r} domains={include_domains} "
                f"→ {len(results)} results"
            )
            out = []
            for r in results:
                out.append(
                    {
                        "url": r.get("url", ""),
                        "title": r.get("title", ""),
                        "text": r.get("text", r.get("content", "")),
                        "summary": r.get("summary", ""),
                        "score": r.get("score", 0.0),
                    }
                )
            return out
        except requests.HTTPError as e:
            logger.warning(
                f"[Exa] HTTP {e.response.status_code} for query={query[:60]!r}: "
                f"{e.response.text[:200]}"
            )
            return []
        except Exception as e:
            logger.warning(f"[Exa] request failed for query={query[:60]!r}: {e}")
            return []

    def search_jobs(self, keyword: str, site: str = "") -> List[Dict]:
        """Convenience: search jobs with salary/location hints."""
        query = f"{keyword} job hiring salary"
        return self.search(query, site=site, limit=self.max_results)
