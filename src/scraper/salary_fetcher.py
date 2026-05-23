"""Direct HTTP fetcher - replaces Firecrawl with requests + browser headers."""
import os
import re
import requests
from typing import Optional

# Browser-like headers to avoid blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "DNT": "1",
}

# Enhanced salary regex - covers more formats
SALARY_RE = re.compile(
    r"(?i)"
    r"(?:"
    # $100,000 - $150,000 / YEAR or $100k-$150k
    r"\$[\d,]+(?:,\d{3})*(?:\s*-\s*\$?[\d,]+(?:,\d{3})*)?(?:\s*/?\s*(?:year|month|hr|hour|YEAR|MONTH|HR|HOUR|年薪|月薪))?"
    r"|"
    # ￥10,000 - ￥20,000
    r"[￥¥][\d,]+(?:,\d{3})*(?:\s*-\s*[￥¥]?[\d,]+(?:,\d{3})*)?(?:\s*/?\s*(?:year|month|YEAR|MONTH|年|月|年薪|月薪))?"
    r"|"
    # 15k-25k, 15K-25K
    r"\d{2,3}\.?\d*\s*[kK]\s*(?:-\s*\d{2,3}\.?\d*\s*[kK])?"
    r"|"
    # 30万-50万, 15万-25万
    r"\d+\.?\d*\s*[万wW](?:\s*[-~到]\s*\d+\.?\d*\s*[万wW])?(?:\s*人民币|\s*yuan|\s*年薪|\s*月薪)?"
    r"|"
    # £40,000 - £50,000
    r"£[\d,]+(?:,\d{3})*(?:\s*-\s*£?[\d,]+(?:,\d{3})*)?"
    r"|"
    # €40,000 - €50,000
    r"€[\d,]+(?:,\d{3})*(?:\s*-\s*€?[\d,]+(?:,\d{3})*)?"
    r"|"
    # CNY 92,995, CNY 92,995/year
    r"CNY\s*[\d,]+(?:,\d{3})*(?:\s*-\s*CNY?\s*[\d,]+(?:,\d{3})*)?(?:\s*/?\s*(?:year|month|hr|hour|YEAR|MONTH|HR|HOUR|年薪|月薪))?"
    r"|"
    # HK$150, HK$150,000
    r"HK\$\s*[\d,]+(?:,\d{3})*(?:\s*-\s*HK\$\s*[\d,]+(?:,\d{3})*)?"
    r")"
)


def extract_salary_from_text(text: str) -> Optional[str]:
    """Extract salary info from any text content."""
    if not text:
        return None
    matches = SALARY_RE.findall(text)
    if matches:
        for match in matches:
            salary = match.strip().rstrip("/,")
            # Filter out obvious false positives: 4-digit year numbers
            # e.g. "2013" or "2024" without currency prefix
            if re.match(r'^\d{4}$', salary):
                continue
            if salary.lower().startswith("20") and len(salary) == 4:
                continue
            # Filter out "20XX w" where XX are digits (year + 万 character)
            if re.match(r'^20\d{2}\s*[万wW]', salary):
                continue
            return salary
    return None


def direct_fetch(url: str, timeout: int = 10) -> Optional[str]:
    """
    Fetch page content directly using requests with browser-like headers.
    Returns the raw text content if successful, None otherwise.
    """
    if not url or not url.strip():
        return None
    try:
        resp = requests.get(url.strip(), headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
    except requests.exceptions.Timeout:
        pass
    except Exception:
        pass
    return None


# Try Firecrawl first (best quality), then direct fetch
def fetch_salary_range(url: str, tavily_content: str = "") -> str:
    """
    Extract salary info from multiple sources in priority order:
    1. Tavily's content field (already fetched, zero cost)
    2. Direct HTTP fetch with browser headers
    3. Firecrawl (API-based, best for complex pages)
    Returns formatted salary string or "N/A"
    """
    # Priority 1: Tavily content already has salary data
    if tavily_content:
        salary = extract_salary_from_text(tavily_content)
        if salary:
            return salary

    # Priority 2: Direct HTTP fetch
    http_content = direct_fetch(url)
    if http_content:
        salary = extract_salary_from_text(http_content)
        if salary:
            return salary

    # Priority 3: Firecrawl fallback
    from src.scraper.firecrawl_client import scrape as firecrawl_scrape
    fc_result = firecrawl_scrape(url, accepted_formats=["text"], timeout=15)
    if fc_result:
        text = fc_result.get("text") or ""
        if text:
            salary = extract_salary_from_text(text)
            if salary:
                return salary

    return "N/A"