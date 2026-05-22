from bs4 import BeautifulSoup
from datetime import datetime, timezone
from ._exceptions import ScraperError

REGISTERED_PARSERS = {}

def register(name):
    def decorator(fn):
        REGISTERED_PARSERS[name] = fn
        return fn
    return decorator

@register("linkedin")
def parse_linkedin(html):
    soup = BeautifulSoup(html, "html.parser")
    try:
        title_elem = soup.select_one(".topcard__title")
        company_elem = soup.select_one(".topcard__org-name-link")
        loc_elem = soup.select_one(".topcard__flavor--bullet")
        desc_elem = soup.select_one(".description__text")
        return {
            "title": title_elem.get_text(strip=True) if title_elem else "",
            "company": company_elem.get_text(strip=True) if company_elem else "",
            "location": loc_elem.get_text(strip=True) if loc_elem else "",
            "posted_date": datetime.now(timezone.utc).isoformat(),
            "description": desc_elem.get_text(strip=True) if desc_elem else "",
        }
    except Exception as exc:
        raise ScraperError(f"LinkedIn parser failed: {exc}") from exc

@register("zhaopin")
def parse_zhaopin(html):
    soup = BeautifulSoup(html, "html.parser")
    try:
        title_elem = soup.select_one(".job-name")
        company_elem = soup.select_one(".company_name a")
        loc_elem = soup.select_one(".job-area")
        desc_elem = soup.select_one(".detail-content")
        return {
            "title": title_elem.get_text(strip=True) if title_elem else "",
            "company": company_elem.get_text(strip=True) if company_elem else "",
            "location": loc_elem.get_text(strip=True) if loc_elem else "",
            "posted_date": datetime.now(timezone.utc).isoformat(),
            "description": desc_elem.get_text(strip=True) if desc_elem else "",
        }
    except Exception as exc:
        raise ScraperError(f"Zhaopin parser failed: {exc}") from exc

@register("51job")
def parse_51job(html):
    soup = BeautifulSoup(html, "html.parser")
    try:
        title_elem = soup.select_one(".t1 span")
        company_elem = soup.select_one(".cname a")
        loc_elem = soup.select_one(".lname")
        desc_elem = soup.select_one("#tmsg")
        return {
            "title": title_elem.get_text(strip=True) if title_elem else "",
            "company": company_elem.get_text(strip=True) if company_elem else "",
            "location": loc_elem.get_text(strip=True) if loc_elem else "",
            "posted_date": datetime.now(timezone.utc).isoformat(),
            "description": desc_elem.get_text(strip=True) if desc_elem else "",
        }
    except Exception as exc:
        raise ScraperError(f"51job parser failed: {exc}") from exc

@register("generic")
def generic_parse(html):
    soup = BeautifulSoup(html, "html.parser")
    try:
        title = soup.title.get_text(strip=True) if soup.title else "Unnamed"
        return {
            "title": title,
            "company": "未知",
            "location": "未知",
            "posted_date": datetime.now(timezone.utc).isoformat(),
            "description": soup.get_text(separator="\n", strip=True)[:500],
        }
    except Exception as exc:
        raise ScraperError(f"Generic parser failed: {exc}") from exc