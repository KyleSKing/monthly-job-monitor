"""
Monthly Job Monitor — 3-Tier Scraper Orchestrator

Search Tier Strategy:
  Tier 1 (Primary):   Exa search → crawl4ai content extraction
  Tier 2 (Secondary): Serper search → Firecrawl content extraction
  Tier 3 (Fallback):  Tavily search → Tavily content extraction

Each tier is tried in order. If Tier 1 returns results for a given keyword/site,
Tier 2 and 3 are skipped for that combo. Results merge and deduplicate at the end.
"""

import concurrent.futures
import json
import os
import sys
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from .config import load_config, ScraperConfig
from .exa_client import ExaClient
from .crawl4ai_client import Crawl4aiClient
from .serper_client import SerperClient
from .tavily_client import TavilyClient
from .firecrawl_client import FirecrawlClient
from .playwright_scraper import PlaywrightScraper
from .parsers import REGISTERED_PARSERS
from .scorer import score_job
from .email_sender import send_email
from ._exceptions import ScraperError

logger = logging.getLogger(__name__)


# ── Site-specific search queries ──────────────────────────────────────
# Tier 1 (Exa) and Tier 2 (Serper) use these; Tier 3 (Tavily) has its own
JOB_QUERIES = [
    # LinkedIn (English, Beijing + Remote) — 重心:信息安全合规/数据合规/隐私
    (
        "linkedin",
        'site:linkedin.com/jobs "security compliance" OR "IT compliance" Beijing OR remote',
    ),
    (
        "linkedin",
        'site:linkedin.com/jobs "data compliance" OR "data governance" Beijing OR remote',
    ),
    (
        "linkedin",
        'site:linkedin.com/jobs "data privacy" OR "privacy officer" OR GDPR Beijing OR remote',
    ),
    (
        "linkedin",
        'site:linkedin.com/jobs "GRC" OR "information security compliance" Beijing OR remote',
    ),
    ("linkedin", 'site:linkedin.com/jobs "information security" Beijing OR remote'),
    # Zhaopin (Chinese, Beijing/Remote)
    (
        "zhaopin",
        "site:zhaopin.com 信息安全合规 OR 数据合规 OR 网络安全合规 北京 OR 远程",
    ),
    ("zhaopin", "site:zhaopin.com 数据安全 OR 数据治理 OR 个人信息保护 北京 OR 远程"),
    ("zhaopin", "site:zhaopin.com 合规经理 OR 等保 OR 隐私合规 北京 OR 远程"),
    # 51Job
    ("51job", "site:51job.com 信息安全合规 OR 数据合规 OR 网络安全合规 北京 OR 远程"),
    ("51job", "site:51job.com 数据安全 OR 个人信息保护 OR 隐私合规 北京 OR 远程"),
    # Liepin
    ("liepin", "site:liepin.com 信息安全合规 OR 数据合规 OR 数据安全 北京 OR 远程"),
    ("liepin", "site:liepin.com 数据治理 OR 个人信息保护 OR 等保 北京 OR 远程"),
    # Lagou
    ("lagou", "site:lagou.com 信息安全合规 OR 数据合规 OR 数据安全 北京 OR 远程"),
    ("lagou", "site:lagou.com 数据治理 OR 隐私合规 OR 个人信息保护 北京 OR 远程"),
]


class TieredScraper:
    """Orchestrates 3-tier scraping: Exa→Jina, Serper→Firecrawl, Tavily."""

    def __init__(self, config_path: str = "config.yaml"):
        self.cfg = load_config(config_path)

        # Initialize all clients (lazy — only used when needed)
        self.exa = ExaClient(
            api_key=self.cfg.exa_api_key, max_results=self.cfg.max_results
        )
        self.reader = Crawl4aiClient(timeout=self.cfg.timeout)
        self.serper = SerperClient(
            api_key=self.cfg.serper_api_key,
            max_results=self.cfg.max_results,
        )
        self.firecrawl = FirecrawlClient(token=self.cfg.firecrawl_token)
        self.tavily = TavilyClient(
            api_key=self.cfg.tavily_api_key, max_results=self.cfg.max_results
        )
        self.playwright = PlaywrightScraper(timeout=self.cfg.timeout * 1000)

    # ── Tier 1: Exa + Jina ────────────────────────────────────

    def _tier1_search(self, site: str, query: str) -> List[Dict]:
        """Tier 1: Exa search → crawl4ai (batch) for content."""
        results = self.exa.search(query, limit=self.cfg.max_results)
        if not results:
            logger.debug(f"[Tier1] Exa returned 0 results for {site}")
            return []

        # Batch-fetch all URLs concurrently instead of one at a time.
        urls = [r.get("url", "") for r in results if r.get("url")]
        content_by_url = self.reader.fetch_many(urls)

        jobs = []
        for r in results:
            url = r.get("url", "")
            title = r.get("title", "") or ""
            text = r.get("text", "") or ""
            summary = r.get("summary", "") or ""

            content = content_by_url.get(url)
            if content:
                description = content[:2000]
            else:
                description = text or summary

            job = {
                "source": f"Exa-{site}",
                "tier": 1,
                "title": title,
                "company": self._extract_company(r, title, url),
                "location": self._extract_location(description, title),
                "salary": self._extract_salary(description, title),
                "url": url,
                "description": description,
                "posted_date": datetime.now().strftime("%Y-%m-%d"),
            }
            jobs.append(job)

        logger.info(f"[Tier1] Exa+crawl4ai: {len(jobs)} jobs from {site}")
        return jobs

    # ── Tier 2: Serper + Firecrawl ──────────────────────────────

    def _tier2_search(self, site: str, query: str) -> List[Dict]:
        """Tier 2: Serper search → Firecrawl for content."""
        results = self.serper.search(query, limit=self.cfg.max_results)
        if not results:
            logger.debug(f"[Tier2] Serper returned 0 results for {site}")
            return []

        jobs = []
        for r in results:
            url = r.get("url", "")
            title = r.get("title", "") or ""
            snippet = r.get("content", r.get("snippet", "")) or ""

            # Firecrawl for rich content
            fc_result = self.firecrawl.scrape(url)
            content = fc_result.get("markdown", fc_result.get("text", ""))
            if content:
                description = content[:2000]
            else:
                description = snippet

            job = {
                "source": f"Serper-{site}",
                "tier": 2,
                "title": title,
                "company": self._extract_company(r, title, url),
                "location": self._extract_location(description, title),
                "salary": self._extract_salary(description, title),
                "url": url,
                "description": description,
                "posted_date": datetime.now().strftime("%Y-%m-%d"),
            }
            jobs.append(job)

        logger.info(f"[Tier2] Serper+Firecrawl: {len(jobs)} jobs from {site}")
        return jobs

    # ── Tier 3: Tavily (Fallback) ──────────────────────────────────

    def _tier3_search(self, site: str, query: str) -> List[Dict]:
        """Tier 3: Tavily search + content extraction."""
        results = self.tavily.search(query, limit=self.cfg.max_results)
        if not results:
            logger.debug(f"[Tier3] Tavily returned 0 results for {site}")
            return []

        jobs = []
        for r in results:
            url = r.get("url", "")
            title = r.get("title", "") or ""
            content = r.get("content", "") or ""
            answer = r.get("tavily_answer", "") or ""

            description = content or answer

            job = {
                "source": f"Tavily-{site}",
                "tier": 3,
                "title": title,
                "company": self._extract_company(r, title, url),
                "location": self._extract_location(description, title),
                "salary": self._extract_salary(description, title),
                "url": url,
                "description": description[:2000],
                "posted_date": datetime.now().strftime("%Y-%m-%d"),
            }
            jobs.append(job)

        logger.info(f"[Tier3] Tavily: {len(jobs)} jobs from {site}")
        return jobs

    # ── CSV targets ────────────────────────────────────────────────

    def _process_csv_target(self, csv_path: str) -> List[Dict]:
        """Read a CSV target and return basic job entries."""
        csv_path_resolved = csv_path
        if not os.path.isabs(csv_path):
            # Resolve relative to project root
            csv_path_resolved = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                csv_path,
            )
        if not os.path.isfile(csv_path_resolved):
            logger.warning(f"CSV not found: {csv_path_resolved}")
            return []

        import csv as csv_module

        jobs = []
        try:
            with open(csv_path_resolved, newline="", encoding="utf-8") as f:
                reader = csv_module.DictReader(f)
                for row in reader:
                    company_url = (
                        row.get("WebURL") or row.get("url") or row.get("website") or ""
                    )
                    company_name = row.get("Company") or row.get("company") or ""
                    if company_url:
                        jobs.append(
                            {
                                "source": "CSV",
                                "tier": 0,
                                "title": f"Various positions at {company_name or company_url.split('/')[-1]}",
                                "company": (
                                    company_name or company_url.split("/")[2]
                                    if "://" in company_url
                                    else company_url.split("/")[0]
                                ),
                                "location": "Beijing",
                                "salary": "N/A",
                                "url": company_url,
                                "description": f"Check {company_url} for available positions.",
                                "posted_date": datetime.now().strftime("%Y-%m-%d"),
                            }
                        )
        except Exception as e:
            logger.error(f"CSV parse error {csv_path}: {e}")
        return jobs

    # ── Pipeline: run all tiers for all queries ────────────────────

    def scrape_all(self) -> List[Dict]:
        """Run the full 3-tier scraping pipeline."""
        all_jobs = []
        seen_site_queries = {}  # site → had results at tier
        tier_hits = {1: 0, 2: 0, 3: 0}  # queries that produced results per tier

        for site, query in JOB_QUERIES:
            site_results = []

            # Tier 1: Exa + Jina
            tier1 = self._tier1_search(site, query)
            if tier1:
                site_results.extend(tier1)
                seen_site_queries[f"{site}:{query}"] = 1
                tier_hits[1] += 1
            else:
                # Tier 2: Serper + Firecrawl
                tier2 = self._tier2_search(site, query)
                if tier2:
                    site_results.extend(tier2)
                    seen_site_queries[f"{site}:{query}"] = 2
                    tier_hits[2] += 1
                else:
                    # Tier 3: Tavily
                    tier3 = self._tier3_search(site, query)
                    if tier3:
                        site_results.extend(tier3)
                        seen_site_queries[f"{site}:{query}"] = 3
                        tier_hits[3] += 1

            all_jobs.extend(site_results)

        logger.info(
            f"Search-tier hits across {len(JOB_QUERIES)} queries — "
            f"Tier1(Exa): {tier_hits[1]}, Tier2(Serper): {tier_hits[2]}, "
            f"Tier3(Tavily): {tier_hits[3]}"
        )

        # ── CSV targets ──
        for target in self.cfg.targets:
            if isinstance(target, dict):
                url = target.get("url", "")
                parser = target.get("parser", "generic")
            else:
                url = getattr(target, "url", "")
                parser = "csv" if url.endswith(".csv") else "generic"

            if parser == "csv":
                all_jobs.extend(self._process_csv_target(url))

        # ── Deduplicate by URL ──
        all_jobs = self._deduplicate(all_jobs)

        # ── Filter: Beijing & remote only ──
        all_jobs = self._filter_location(all_jobs)

        # ── Score ──
        for job in all_jobs:
            job["Score"] = score_job(job)

        # Sort by Score descending
        all_jobs.sort(key=lambda x: x.get("Score", 0), reverse=True)

        # ── Report tier usage ──
        tier_counts = {1: 0, 2: 0, 3: 0, 0: 0}
        for j in all_jobs:
            tier_counts[j.get("tier", 3)] += 1
        logger.info(
            f"Tier usage — Exa+crawl4ai: {tier_counts[1]}, "
            f"Serper+Firecrawl: {tier_counts[2]}, "
            f"Tavily: {tier_counts[3]}, CSV: {tier_counts[0]}"
        )

        # Release the crawl4ai browser/event loop
        self.reader.close()

        return all_jobs

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _extract_company(result: dict, title: str, url: str) -> str:
        """Try to extract company name from result, title, or URL."""
        # Try result-level company field
        company = result.get("company", "") or ""
        if company and company != "Unknown":
            return company

        # Try title patterns: "Title at Company", "Title - Company"
        for sep in [" at ", " - ", " | ", " @ ", " – ", " — ", " · "]:
            if sep in title:
                parts = title.split(sep, 1)
                company = parts[1].strip()
                if company:
                    return company

        # Try URL domain
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            hostname = parsed.netloc or parsed.path.split("/")[0]
            hostname = hostname.replace("www.", "")
            domain = hostname.split(".")[0] if hostname.count(".") >= 1 else hostname
            known = {
                "linkedin": "LinkedIn",
                "zhaopin": "Zhaopin",
                "51job": "51Job",
                "liepin": "Liepin",
                "lagou": "Lagou",
                "indeed": "Indeed",
            }
            return known.get(domain.lower(), domain.capitalize())
        except Exception:
            return "Unknown"

    @staticmethod
    def _extract_location(content: str, title: str) -> str:
        """Extract location from content."""
        text = (content + " " + title).lower()
        if any(kw in text for kw in ["beijing", "北京"]):
            return "Beijing"
        if any(kw in text for kw in ["remote", "远程", "线上", "异地"]):
            return "Remote"
        if any(kw in text for kw in ["shanghai", "上海"]):
            return "Shanghai"
        if any(kw in text for kw in ["shenzhen", "深圳", "guangzhou", "广州"]):
            return "Shenzhen/Guangzhou"
        # Try regex pattern for location field
        import re

        m = re.search(r"(?:地点|位置|工作地点|location)[：:]\s*([^，。,\n]+)", content)
        if m:
            return m.group(1).strip()
        return "Beijing"  # default

    @staticmethod
    def _extract_salary(content: str, title: str) -> str:
        """Extract salary info from content."""
        if not content:
            return "N/A"
        import re

        patterns = [
            r"(?:薪资|工资|月薪|年薪|salary|compensation)[：:]\s*([^，。,\n]{2,30})",
            r"(¥|$|€|£)?\s*(\d{1,3}(?:,\d{3})*(?:-\d{1,3}(?:,\d{3})?)?)\s*(?:元|K|千|万|w|k|/月|/年)",
            r"(\d{4,5})\s*(?:元|K)",
        ]
        for pat in patterns:
            m = re.search(pat, content, re.IGNORECASE)
            if m:
                return m.group(0).strip()
        return "N/A"

    @staticmethod
    def _deduplicate(jobs: List[Dict]) -> List[Dict]:
        """Deduplicate by URL, keeping highest-tier version."""
        seen = {}
        for job in jobs:
            url = job.get("url", "")
            if not url:
                continue
            tier = job.get("tier", 99)
            if url not in seen or tier < seen[url].get("tier", 99):
                seen[url] = job
        return list(seen.values())

    @staticmethod
    def _filter_location(jobs: List[Dict]) -> List[Dict]:
        """Filter to Beijing & remote only."""
        keywords = [
            "beijing",
            "北京",
            "remote",
            "远程",
            "线上",
            "异地",
            "united states",
            "nationwide",
            "remote -",
            "(remote)",
        ]
        filtered = []
        for j in jobs:
            loc = (j.get("location", "") or "").lower()
            if any(kw in loc for kw in keywords):
                filtered.append(j)
        return filtered


def main():
    """Entry point for the 3-tier scraper."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("scraper.main")

    scraper = TieredScraper()
    jobs = scraper.scrape_all()

    print(f"\n{'='*60}")
    print(f"Total jobs found: {len(jobs)}")
    print(f"{'='*60}")

    # Print top 10
    for rank, job in enumerate(jobs[:10], 1):
        print(f"\n{rank}. {job.get('title', 'N/A')}")
        print(f"   Company: {job.get('company', 'N/A')}")
        print(f"   Location: {job.get('location', 'N/A')}")
        print(f"   Salary: {job.get('salary', 'N/A')}")
        print(f"   Source: {job.get('source', 'N/A')} (Tier {job.get('tier', '?')})")
        print(f"   Score: {job.get('Score', 0):.1f}")
        print(f"   URL: {job.get('url', '#')}")

    # Save reports (repo-root/reports, what the API + clients read)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    reports_dir = os.path.join(project_root, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    output_path = os.path.join(reports_dir, "jobs.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"\nAll jobs saved to {output_path}")

    # Monthly markdown report (recruitment_report_YYYY-MM.md) for humans
    from src.main import generate_report

    generate_report(jobs, output_dir=reports_dir)

    # Top 10 markdown
    top10 = jobs[:10]
    md = "# 🔥 Top 10 Jobs (3-Tier Scraper)\n\n"
    md += f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n"
    for rank, job in enumerate(top10, 1):
        md += f"## {rank}. {job.get('title', 'N/A')}\n\n"
        md += f"- **Company:** {job.get('company', 'N/A')}\n"
        md += f"- **Location:** {job.get('location', 'N/A')}\n"
        md += f"- **Salary:** {job.get('salary', 'N/A')}\n"
        md += (
            f"- **Source:** {job.get('source', 'N/A')} (Tier {job.get('tier', '?')})\n"
        )
        md += f"- **Score:** {job.get('Score', 0):.1f}\n"
        md += f"- **Apply:** [Job Posting]({job.get('url', '#')})\n\n"
        desc = (job.get("description", "") or "")[:300]
        if desc:
            md += f"> {desc.replace(chr(10), ' ').strip()}...\n\n"
        md += "---\n\n"

    md_path = os.path.join(reports_dir, "top10.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Top 10 report saved to {md_path}")


if __name__ == "__main__":
    main()
