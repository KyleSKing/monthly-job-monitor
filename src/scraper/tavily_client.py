"""Tavily search client for fallback job fetching."""
import json
import re
import requests
from typing import List, Dict

TAVILY_API_KEY = "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"
TAVILY_ENDPOINT = "https://api.tavily.com/search"


def search_jobs(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search for jobs using Tavily API.
    Returns a list of result dicts (each contains 'url' and 'title').
    """
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
    }
    try:
        resp = requests.post(TAVILY_ENDPOINT, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except Exception as e:
        # Fail silently to avoid breaking the pipeline
        print(f"[Tavily fallback] Search failed for '{query}': {e}")
        return []


def extract_keywords_from_url(url: str) -> str:
    """
    Extract keywords from a URL.
    """
    if "keywords=" not in url:
        return url.split("?")[0]
    raw = url.split("keywords=")[1]
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", raw)
    return cleaned


def fallback_fetch(target_url: str) -> List[str]:
    """
    Get candidate URLs via Tavily when primary fetch fails.
    """
    keywords = extract_keywords_from_url(target_url)
    raw_keywords = keywords.strip()
    if not raw_keywords:
        return []
    query = f"{raw_keywords} job Beijing"
    results = search_jobs(query, max_results=3)
    urls = [r["url"] for r in results if "job" in r.get("url", "").lower() or "career" in r.get("url", "").lower()]
    return urls[:2]