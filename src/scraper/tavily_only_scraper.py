"""Job scraper with Tavily API and 3-tier salary extraction."""

import csv
import os
import json
import re
from urllib.parse import urlparse
from src.scraper.config import load_config
from src.scraper.tavily_client import search_jobs, extract_keywords_from_url
from src.scraper.scorer import score_job
from src.scraper.salary_fetcher import fetch_salary_range


def parse_csv(csv_path: str) -> list:
    """Read CSV and return company website URLs."""
    urls = []
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), csv_path
        )
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("WebURL") or row.get("url") or row.get("website")
                if url:
                    urls.append(url.strip())
    except FileNotFoundError:
        print(f"[WARN] CSV file not found: {csv_path}")
    except Exception as e:
        print(f"[WARN] Failed to read CSV {csv_path}: {e}")
    return urls


def extract_company_from_url(url: str) -> str:
    """Extract company name from a URL hostname with smart naming."""
    try:
        parsed = urlparse(url)
        hostname = parsed.netloc or parsed.path.split("/")[0]
        # Remove www. prefix
        name = hostname.replace("www.", "")
        # Remove common TLDs for domain-based names
        domain = name.split(".")[0] if name.count(".") >= 1 else name
        # Special cases for known domains
        known_names = {
            "roberthalf": "Robert Half",
            "salaryexpert": "SalaryExpert",
            "salary": "Salary.com",
            "erieri": "ERI",
            "redbudcyber": "RedBud Cyber",
            "neit": "NEIT",
            "usnews": "U.S. News",
            "glassdoor": "Glassdoor",
            "linkedin": "LinkedIn",
            "indeed": "Indeed",
            "adp": "ADP",
            "ecovis": "Ecovis",
        }
        for key, val in known_names.items():
            if key in name.lower() or key in domain.lower():
                return val
        # Generic: capitalize first letter
        return domain.capitalize() if domain else "Unknown"
    except Exception:
        return "Unknown"


def extract_company_from_title(title: str) -> str:
    """Try to extract company name from job title patterns like 'at Company', '- Company'."""
    patterns = [
        r"(?:at|@|with|at )\s+([A-Z][A-Za-z0-9\s.&]+?)(?:\s*[-–—|]\s*|\s*$)",
        r"^([A-Z][A-Za-z0-9\s.&]+?)\s*(?:is hiring|hiring|seeking|looking for)",
        r"[-–—|]\s*([A-Z][A-Za-z0-9\s.&]{2,30}?)\s*$",
    ]
    for pat in patterns:
        m = re.search(pat, title)
        if m:
            return m.group(1).strip()
    return None


def build_job(r: dict) -> dict:
    """Build a normalized job dict from a Tavily result."""
    content = r.get("content", "")
    title = r.get("title", "Unknown")
    url = r.get("url", "")

    # Determine company name: try Tavily's field, extract from title, or fall back to URL
    company = r.get("company") or ""
    if not company or company == "Unknown":
        company = extract_company_from_title(title) or extract_company_from_url(url)

    # Determine location: try Tavily's field or extract from content
    location = r.get("location", "")
    if not location or location == "Unknown":
        # Look for Beijing/China/remote in first 200 chars of content
        location_text = content[:300]
        for loc_keyword in ["Beijing", "北京", "China", "中国", "Remote", "远程"]:
            if loc_keyword.lower() in location_text.lower():
                location = loc_keyword
                break
        if not location:
            location = "Beijing"  # default

    job = {
        "title": title,
        "company": company or "Unknown",
        "location": location,
        "url": url,
        "description": content,
    }

    # Extract salary: Tier 1 from Tavily content, Tier 2 direct fetch, Tier 3 Firecrawl
    job["salary_range"] = fetch_salary_range(url, tavily_content=content)

    # Our custom score
    job["Score"] = score_job(job)
    job["tavily_relevance_score"] = r.get("score", 0.0)

    return job


def deduplicate(jobs: list) -> list:
    """Remove duplicates by URL, keeping the highest scoring version."""
    seen = {}
    for job in jobs:
        url = job.get("url", "")
        if not url:
            continue
        score = job.get("Score", 0)
        if url not in seen or score > seen[url].get("Score", 0):
            seen[url] = job
    return list(seen.values())


def format_salary_short(salary: str) -> str:
    """Convert long salary strings to short display. e.g. '$100,000 - $150,000' -> '$100k-150k'"""
    if not salary or salary == "N/A":
        return "N/A"
    # Already short
    if len(salary) < 20:
        return salary
    # Try to compress
    numbers = re.findall(r"[\d,]+", salary)
    currency = re.match(r"[¥$£€]", salary)
    prefix = currency.group(0) if currency else ""
    if len(numbers) >= 2:
        return f"{prefix}{numbers[0]}-{numbers[1]}"
    return salary[:30]


def main():
    cfg = load_config()
    all_jobs = []

    for target in cfg.targets:
        if isinstance(target, dict):
            url = target.get("url") or ""
            parser = target.get("parser", "generic")
        else:
            url = getattr(target, "url", "")
            parser = "csv" if url.endswith(".csv") else "generic"

        if not url:
            continue

        if parser == "csv":
            company_urls = parse_csv(url)
            for company_url in company_urls:
                job = {
                    "title": f"Various positions at {company_url.split('/')[-1]}",
                    "company": (
                        company_url.split("/")[2]
                        if "://" in company_url
                        else company_url.split("/")[0]
                    ),
                    "location": "Beijing",
                    "url": company_url,
                    "description": f"Check {company_url} for available positions.",
                    "salary_range": "N/A",
                    "tavily_relevance_score": 0.0,
                }
                job["Score"] = score_job(job)
                all_jobs.append(job)
        else:
            keywords = extract_keywords_from_url(url)
            # Search with salary keywords to improve salary hit rate
            results = search_jobs(
                f"{keywords} job Beijing salary compensation", max_results=10
            )
            for r in results:
                job = build_job(r)
                all_jobs.append(job)

    # Deduplicate by URL
    all_jobs = deduplicate(all_jobs)

    # Sort by Score descending
    all_jobs.sort(key=lambda x: x.get("Score", 0), reverse=True)
    top_jobs = all_jobs[:10]

    reports_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "reports")
    )
    os.makedirs(reports_dir, exist_ok=True)

    # ---- Write full jobs.json ----
    full_out = os.path.join(reports_dir, "jobs.json")
    with open(full_out, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)
    print(f"\n[RESULT] Found {len(all_jobs)} jobs (after dedup), saved to {full_out}")

    # ---- Write top10.json ----
    top10_json = os.path.join(reports_dir, "top10.json")
    json_output = []
    for rank, job in enumerate(top_jobs, 1):
        entry = {
            "rank": rank,
            "title": job.get("title", "N/A"),
            "company": job.get("company", "N/A"),
            "location": job.get("location", "N/A"),
            "apply_url": job.get("url", "N/A"),
            "salary_range": job.get("salary_range", "N/A"),
            "score": job.get("Score", 0),
            "salary_score": job.get("Score", 0),  # salary component embedded in score
            "description": (
                (job.get("description", "") or "")[:200] + "..."
                if len((job.get("description", "") or "")) > 200
                else (job.get("description", "") or "")
            ),
        }
        json_output.append(entry)

    with open(top10_json, "w", encoding="utf-8") as f:
        json.dump(json_output, f, ensure_ascii=False, indent=2)
    print(f"Top 10 JSON report written to {top10_json}")

    # ---- Write top10.md ----
    md = "# 🔥 Top 10 Jobs by Score\n\n"
    md += f"_Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n"

    for rank, job in enumerate(top_jobs, 1):
        title = job.get("title", "N/A")
        company = job.get("company", "N/A")
        location = job.get("location", "N/A")
        score = job.get("Score", 0)
        url = job.get("url", "N/A")
        salary = job.get("salary_range", "N/A")
        desc = job.get("description", "") or ""

        # Salary highlight
        if salary and salary != "N/A":
            salary_display = f"💰 **{salary}**"
        else:
            salary_display = "❓ Salary not specified"

        md += f"## {rank}. {title}\n\n"
        md += f"| | |\n|---|---|\n"
        md += f"| **Company** | {company} |\n"
        md += f"| **Location** | {location} |\n"
        md += f"| **Score** | {score}/10 |\n"
        md += f"| {salary_display} | |\n"
        md += f"| **Apply** | [Open Job Posting]({url}) |\n"

        # Brief excerpt
        if desc:
            excerpt = desc[:300].replace("\n", " ").strip()
            md += f"\n> {excerpt}...\n"
        md += "\n---\n\n"

    top10_md = os.path.join(reports_dir, "top10.md")
    with open(top10_md, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Top 10 markdown report written to {top10_md}")


if __name__ == "__main__":
    main()
