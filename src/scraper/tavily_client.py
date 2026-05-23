"""Tavily search client for job fetching and salary extraction."""
import json
import re
import requests
from typing import List, Dict

TAVILY_API_KEY = "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"
TAVILY_ENDPOINT = "https://api.tavily.com/search"


def search_jobs(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search for jobs using Tavily API with content extraction.
    Returns a list of result dicts (each contains 'url', 'title', 'content', 'score').
    """
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "include_answer": True,          # Get AI-summarized answer with salary context
        "search_depth": "advanced",       # Deep search for richer content
    }
    try:
        resp = requests.post(TAVILY_ENDPOINT, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        # Add the answer field to results if present (contains salary summary)
        answer = data.get("answer", "")
        for r in results:
            r["tavily_answer"] = answer
        return results
    except Exception as e:
        print(f"[Tavily] Search failed for '{query}': {e}")
        return []


def extract_keywords_from_url(url: str) -> str:
    """Extract keywords from a URL for search."""
    if "keywords=" not in url:
        return url.split("?")[0]
    raw = url.split("keywords=")[1]
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", raw)
    return cleaned


def fallback_fetch(target_url: str) -> List[str]:
    """Get candidate URLs via Tavily when primary fetch fails."""
    keywords = extract_keywords_from_url(target_url)
    raw_keywords = keywords.strip()
    if not raw_keywords:
        return []
    query = f"{raw_keywords} job Beijing"
    results = search_jobs(query, max_results=3)
    urls = [r["url"] for r in results if "job" in r.get("url", "").lower() or "career" in r.get("url", "").lower()]
    return urls[:2]