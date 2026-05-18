#!/usr/bin/env python3
"""
Job Scraper Module
Scrapes job listings from various job search websites
"""

import logging
import time
import random
import re
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright
import yaml
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class JobScraper:
    """Main scraper class for job listings"""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize scraper with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.scraper_config = self.config.get('scraper', {})
        self.targets = self.scraper_config.get('targets', [])
        self.request_delay = self.scraper_config.get('request_delay', 2)
        self.timeout = self.scraper_config.get('timeout', 30)
        self.max_results = self.scraper_config.get('max_results', 50)
        
        # Tavily integration
        self.use_tavily = self.scraper_config.get('use_tavily', True)
        self.tavily_keywords = self.scraper_config.get('tavily_keywords', 
            ["security engineer", "information security", "cyber security"])
        self.tavily_api_key = self.config.get('tavily', {}).get('api_key', '')

        self.ua = UserAgent()
        self.session = requests.Session()

    def _get_headers(self) -> Dict:
        """Generate random user agent headers"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    def _fetch_page_static(self, url: str, retry_count: int = 0) -> Optional[str]:
        """Fetch a web page with error handling and retries. Falls back to Playwright on 403."""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            time.sleep(self.request_delay + random.uniform(0, 1))
            return response.text
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 403:
                logger.info(f"403 on {url}, falling back to Playwright...")
                return self._fetch_page_playwright(url)
            if retry_count < 3:
                logger.warning(f"Retry {retry_count + 1} for {url}: {e}")
                time.sleep(2 ** retry_count)
                return self._fetch_page_static(url, retry_count + 1)
            logger.error(f"Error fetching {url}: {e}")
            return None
        except requests.RequestException as e:
            if retry_count < 3:
                logger.warning(f"Retry {retry_count + 1} for {url}: {e}")
                time.sleep(2 ** retry_count)
                return self._fetch_page_static(url, retry_count + 1)
            logger.error(f"Error fetching {url}: {e}")
            return None

    def _fetch_page_playwright(self, url: str) -> Optional[str]:
        """Fetch page using Playwright for JS rendering with extra waits and UA."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    ]
                )
                page = browser.new_page()
                page.goto(url, timeout=90000)
                try:
                    page.wait_for_selector("div.job-list, .position-list-item, .result-list", timeout=60000)
                except Exception:
                    page.wait_for_load_state("networkidle")
                html = page.content()
                browser.close()
                return html
        except Exception as e:
            logger.error(f"Playwright error for {url}: {e}")
            return None

    def _search_tavily(self, query: str, limit: int = 5) -> List[Dict]:
        """Search using Tavily API."""
        try:
            if not self.tavily_api_key:
                logger.warning("No Tavily API key configured")
                return []
            
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "limit": limit
            }
            
            try:
                response = requests.post(
                    "https://api.tavily.com/search",
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                return response.json().get('results', [])
            except requests.RequestException as e:
                logger.error(f"Tavily API request failed: {e}")
                return []
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing Tavily response: {e}")
                return []
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return []

    def _parse_linkedin(self, html: str) -> List[Dict]:
        """Parse LinkedIn job search results page."""
        jobs = []
        soup = BeautifulSoup(html, 'lxml')
        # LinkedIn 2024+ structure: base-search-card
        job_cards = soup.find_all('div', class_='base-search-card')
        if not job_cards:
            job_cards = soup.select('li div.job-search-card, div.base-card--link')
        for card in job_cards[:self.max_results]:
            try:
                title_el = card.find('h3', class_='base-search-card__title') or card.find(['h3', 'span'], string=True)
                company_el = card.find('h4', class_='base-search-card__subtitle') or card.find('a', class_='hidden-nested-link')
                location_el = card.find('span', class_='job-search-card__location')
                date_el = card.find('time', class_='job-search-card__listdate')
                link_el = card.find('a', class_='base-card__full-link') or card.find('a', href=True)
                
                title = title_el.get_text(strip=True) if title_el else ''
                if not title:
                    continue
                    
                job = {
                    'source': 'LinkedIn',
                    'title': title,
                    'company': company_el.get_text(strip=True) if company_el else 'N/A',
                    'location': location_el.get_text(strip=True) if location_el else 'N/A',
                    'url': link_el.get('href', '').split('?')[0] if link_el else '#',
                    'posted_date': date_el.get('datetime', datetime.now().strftime('%Y-%m-%d')) if date_el else datetime.now().strftime('%Y-%m-%d'),
                    'salary': 'N/A',
                }
                jobs.append(job)
            except Exception as e:
                logger.debug(f"Error parsing LinkedIn card: {e}")
        return jobs

    def _parse_indeed(self, html: str) -> List[Dict]:
        jobs = []
        soup = BeautifulSoup(html, 'lxml')
        job_cards = soup.find_all('div', class_='job-card')
        for card in job_cards[:self.max_results]:
            try:
                job = {
                    'source': 'Indeed',
                    'title': card.find('h3', class_='job-card-list__title').text.strip() if card.find('h3', class_='job-card-list__title') else 'N/A',
                    'company': card.find('span', class_='job-card-container__company-name').text.strip() if card.find('span', class_='job-card-container__company-name') else 'N/A',
                    'location': card.find('li', class_='job-card-container__metadata-item').text.strip() if card.find('li', class_='job-card-container__metadata-item') else 'N/A',
                    'url': card.find('a', class_='job-card-list__title').get('href') if card.find('a', class_='job-card-list__title') else '#',
                    'posted_date': card.find('span', class_='date').text.strip() if card.find('span', class_='date') else datetime.now().strftime('%Y-%m-%d')
                }
                if job['title']:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"Error parsing Indeed card: {e}")
        return jobs

    def _parse_zhaopin(self, html: str) -> List[Dict]:
        jobs = []
        soup = BeautifulSoup(html, 'lxml')
        job_cards = soup.select('div.job-list, .position-list-item')
        for card in job_cards[:self.max_results]:
            try:
                title_elem = card.select_one('h3, .title')
                company_elem = card.select_one('.company, .company-name')
                location_elem = card.select_one('.location, .city')
                salary_elem = card.select_one('.salary, .pay')
                link_elem = card.select_one('a')
                title = title_elem.get_text(strip=True) if title_elem else 'N/A'
                company = company_elem.get_text(strip=True) if company_elem else 'N/A'
                location = location_elem.get_text(strip=True) if location_elem else 'N/A'
                salary = salary_elem.get_text(strip=True) if salary_elem else 'N/A'
                url = link_elem['href'] if link_elem and link_elem.has_attr('href') else '#'
                job = {
                    'source': 'Zhaopin',
                    'title': title,
                    'company': company,
                    'location': location,
                    'salary': salary,
                    'url': url,
                    'posted_date': datetime.now().strftime('%Y-%m-%d'),
                    'benefits': self._extract_benefits(card.get_text()),
                    'work_env': 'office',
                    'career_growth': 'moderate'
                }
                jobs.append(job)
            except Exception as e:
                logger.debug(f"Error parsing Zhaopin card: {e}")
        return jobs

    def _parse_51job(self, html: str) -> List[Dict]:
        jobs = []
        soup = BeautifulSoup(html, 'lxml')
        job_cards = soup.select('div.joblist, .job-item')
        for card in job_cards[:self.max_results]:
            try:
                title_elem = card.select_one('h3, .title, .job-name')
                company_elem = card.select_one('.company, .comp-Name')
                location_elem = card.select_one('.location, .city')
                salary_elem = card.select_one('.salary, .pay')
                link_elem = card.select_one('a')
                title = title_elem.get_text(strip=True) if title_elem else 'N/A'
                company = company_elem.get_text(strip=True) if company_elem else 'N/A'
                location = location_elem.get_text(strip=True) if location_elem else 'N/A'
                salary = salary_elem.get_text(strip=True) if salary_elem else 'N/A'
                url = link_elem['href'] if link_elem and link_elem.has_attr('href') else '#'
                job = {
                    'source': '51Job',
                    'title': title,
                    'company': company,
                    'location': location,
                    'salary': salary,
                    'url': url,
                    'posted_date': datetime.now().strftime('%Y-%m-%d'),
                    'benefits': self._extract_benefits(card.get_text()),
                    'work_env': 'office',
                    'career_growth': 'moderate'
                }
                jobs.append(job)
            except Exception as e:
                logger.debug(f"Error parsing 51Job card: {e}")
        return jobs

    def _generic_parse(self, html: str, source_name: str) -> List[Dict]:
        jobs = []
        soup = BeautifulSoup(html, 'lxml')
        for card in soup.select('div.job-card, li.result')[:self.max_results]:
            try:
                title = card.select_one('h2, h3, .title')
                company = card.select_one('.company, .company-name')
                location = card.select_one('.location, .city')
                salary = card.select_one('.salary')
                posted = card.select_one('.date, .post-date')
                link = card.select_one('a')
                job = {
                    'source': source_name,
                    'title': title.get_text(strip=True) if title else 'N/A',
                    'company': company.get_text(strip=True) if company else 'N/A',
                    'location': location.get_text(strip=True) if location else 'N/A',
                    'salary': salary.get_text(strip=True) if salary else 'N/A',
                    'url': link['href'] if link and link.has_attr('href') else '#',
                    'posted_date': posted.get_text(strip=True) if posted else datetime.now().strftime('%Y-%m-%d')
                }
                jobs.append(job)
            except Exception as e:
                logger.debug(f"Generic parse error: {e}")
        return jobs

    def _extract_salary(self, text: str) -> str:
        if not text:
            return 'N/A'
        patterns = [
            r'(\d{1,3}(?:,\d{3})+)\s*(?:元|K|千|万|w|yuan)',
            r'(?:月薪|年薪|薪资|待遇)[^，。]*?(\d{1,3}(?:,\d{3})+(?:-\d{1,3}(?:,\d{3})?)?)\s*(?:元|K)',
            r'(\d{4,5})\s*(?:元|K)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return 'N/A'

    def _extract_benefits(self, text: str) -> Dict:
        benefits = {'medical': 0, 'stock': 0, 'retirement': 0, 'bonus': 0}
        if not text:
            return benefits
        text_lower = text.lower()
        if any(x in text_lower for x in ['医疗', '医保', 'health', 'medical']):
            benefits['medical'] = 1
        if any(x in text_lower for x in ['五险', '全保', 'insurance']):
            benefits['medical'] = 2
        if any(x in text_lower for x in ['股票', '股份', 'stock', 'equity']):
            benefits['stock'] = 1
        if any(x in text_lower for x in ['期权', 'options']):
            benefits['stock'] = 2
        if any(x in text_lower for x in ['养老', '退休', 'pension', 'retirement']):
            benefits['retirement'] = 1
        if any(x in text_lower for x in ['奖金', '绩效', 'bonus', 'performance']):
            benefits['bonus'] = 1
        return benefits

    def scrape_all(self) -> List[Dict]:
        all_jobs = []
        if self.use_tavily:
            # Targeted site searches for actual job listing pages
            job_site_queries = [
                ("linkedin", 'site:linkedin.com/jobs "security engineer" hiring 2026'),
                ("linkedin", 'site:linkedin.com/jobs "cyber security" engineer'),
                ("linkedin", 'site:linkedin.com/jobs "cloud security" engineer'),
                ("linkedin", 'site:linkedin.com/jobs "application security" engineer'),
            ]
            seen_urls = set()
            
            for site, query in job_site_queries:
                logger.info(f"Tavily searching [{site}]: {query}")
                tavily_results = self._search_tavily(query, limit=5)
                for result in tavily_results:
                    url = result.get('url', '')
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    logger.info(f"Fetching URL from Tavily: {url}")
                    html = self._fetch_page_static(url)
                    if not html:
                        continue
                    if 'indeed' in url.lower():
                        jobs = self._parse_indeed(html)
                    elif 'linkedin' in url.lower():
                        jobs = self._parse_linkedin(html)
                    elif 'zhaopin' in url.lower():
                        jobs = self._parse_zhaopin(html)
                    elif '51job' in url.lower():
                        jobs = self._parse_51job(html)
                    else:
                        jobs = self._generic_parse(html, result.get('title', 'Unknown'))
                    for job in jobs:
                        job['source'] = f"Tavily-{job.get('source', 'Web')}"
                        all_jobs.append(job)
                    logger.info(f"Found {len(jobs)} jobs from {url}")
        else:
            for target in self.targets:
                if not target.get('enabled', True):
                    logger.info(f"Skipping disabled source: {target['name']}")
                    continue
                logger.info(f"Scraping: {target['name']}")
                url = target.get('url')
                if not url:
                    logger.warning(f"No URL found for {target['name']}, skipping")
                    continue
                html = self._fetch_page_static(url, retry_count=0)
                if not html:
                    continue
                name_lower = target['name'].lower()
                if 'linkedin' in name_lower:
                    jobs = self._parse_linkedin(html)
                elif 'indeed' in name_lower:
                    jobs = self._parse_indeed(html)
                elif 'zhaopin' in name_lower:
                    jobs = self._parse_zhaopin(html)
                elif '51job' in name_lower:
                    jobs = self._parse_51job(html)
                else:
                    jobs = self._generic_parse(html, target['name'])
                all_jobs.extend(jobs)
                logger.info(f"Found {len(jobs)} jobs from {target['name']}")

        # Deduplicate by title + company
        seen = set()
        deduped = []
        for j in all_jobs:
            key = (j.get('title', ''), j.get('company', ''))
            if key not in seen:
                seen.add(key)
                deduped.append(j)
        logger.info(f"Deduped: {len(all_jobs)} -> {len(deduped)} unique jobs")
        return deduped

def main():
    logging.basicConfig(level=logging.INFO)
    scraper = JobScraper()
    jobs = scraper.scrape_all()
    print(f"\nTotal jobs found: {len(jobs)}")
    for job in jobs[:5]:
        print(f"- {job.get('title')} at {job.get('company')} ({job.get('source')})")

if __name__ == '__main__':
    main()