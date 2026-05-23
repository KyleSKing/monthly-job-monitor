"""Firecrawl client wrapper - optimized for salary extraction."""
import os
import json
import requests

FIRECRAWL_API = "https://api.firecrawl.dev/v1/scrape"
FIRECRAWL_TOKEN = os.getenv("FIRECRAWL_TOKEN") or "fc-bdf1c041f9dc48688ae9b24767f65298"

def scrape(url: str, accepted_formats: list = ["markdown"], timeout: int = 30):
    """Scrape a single URL with Firecrawl.
    
    Returns a dict with `markdown`, `text`, and `metadata` keys.
    If the URL is empty or invalid, returns empty dict.
    """
    if not url or not url.strip():
        return {"markdown": "", "text": ""}
    
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url.strip(),
        "formats": accepted_formats,
        "pageOptions": {
            "timeout": timeout * 1000,  # milliseconds
            "waitFor": 1000,
        },
    }
    
    try:
        resp = requests.post(FIRECRAWL_API, headers=headers, json=payload, timeout=timeout + 10)
        resp.raise_for_status()
        result = resp.json()
        return result
    except requests.exceptions.Timeout:
        print(f"[WARN] Firecrawl timeout for {url}")
        return {"markdown": "", "text": ""}
    except requests.exceptions.HTTPError as e:
        print(f"[WARN] Firecrawl HTTP error for {url}: {e}")
        return {"markdown": "", "text": ""}
    except Exception as e:
        print(f"[WARN] Firecrawl error for {url}: {e}")
        return {"markdown": "", "text": ""}