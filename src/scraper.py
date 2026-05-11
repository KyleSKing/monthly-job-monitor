#!/usr/bin/env python3
"""
Job Scraper Module
Scrapes job listings from various job search websites
"""

import logging
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import yaml
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
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page with error handling"""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Respect rate limiting
            time.sleep(self.request_delay + random.uniform(0, 1))
            
            return response.text
            
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def _parse_linkedin(self, html: str) -> List[Dict]:
        """Parse LinkedIn job listings"""
        jobs = []
        soup = BeautifulSoup(html, 'lxml')
        
        # Note: LinkedIn requires authentication for most job data
        # This is a simplified parser - may need adjustment
        job_cards = soup.find_all('div', class_='job-card-container')
        
        for card in job_cards[:self.max_results]:
            try:
                job = {
                    'source': 'LinkedIn',
                    'title': card.find('h3', class_='job-card-list__title')?.text.strip(),
                    'company': card.find('span', class_='job-card-container__company-name')?.text.strip(),
                    'location': card.find('li', class_='job-card-container__metadata-item')?.text.strip(),
                    'url': card.find('a', class_='job-card-list__title')?.get('href'),
                    'posted_date': datetime.now().strftime('%Y-%m-%d')
                }
                if job['title']:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"Error parsing LinkedIn card: {e}")
        
        return jobs
    
    def _parse_indeed(self, html: str) -> List[Dict]:
        """Parse Indeed job listings"""
        jobs = []
        soup = BeautifulSoup(html, 'lxml')
        
        job_cards = soup.find_all('div', class_='job-card')
        
        for card in job_cards[:self.max_results]:
            try:
                job = {
                    'source': 'Indeed',
                    'title': card.find('h2', class_='jobTitle')?.text.strip(),
                    'company': card.find('span', class_='companyName')?.text.strip(),
                    'location': card.find('div', class_='companyLocation')?.text.strip(),
                    'salary': card.find('div', class_='salary-snippet')?.text.strip(),
                    'url': 'https://www.indeed.com' + card.find('a', class_='jobTitle')?.get('href', ''),
                    'posted_date': card.find('span', class_='date')?.text.strip() or datetime.now().strftime('%Y-%m-%d')
                }
                if job['title']:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"Error parsing Indeed card: {e}")
        
        return jobs
    
    def scrape_all(self) -> List[Dict]:
        """Scrape all enabled job sources"""
        all_jobs = []
        
        for target in self.targets:
            if not target.get('enabled', True):
                logger.info(f"Skipping disabled source: {target['name']}")
                continue
            
            logger.info(f"Scraping: {target['name']}")
            html = self._fetch_page(target['url'])
            
            if not html:
                continue
            
            # Route to appropriate parser
            if 'linkedin' in target['name'].lower():
                jobs = self._parse_linkedin(html)
            elif 'indeed' in target['name'].lower():
                jobs = self._parse_indeed(html)
            else:
                # Generic parsing
                jobs = self._generic_parse(html, target['name'])
            
            all_jobs.extend(jobs)
            logger.info(f"Found {len(jobs)} jobs from {target['name']}")
        
        return all_jobs
    
    def _generic_parse(self, html: str, source_name: str) -> List[Dict]:
        """Generic parser fallback"""
        # Basic implementation - can be extended
        return []
    
    def filter_by_keywords(self, jobs: List[Dict], keywords: List[str]) -> List[Dict]:
        """Filter jobs by keywords"""
        filtered = []
        for job in jobs:
            title = (job.get('title') or '').lower()
            company = (job.get('company') or '').lower()
            
            for keyword in keywords:
                if keyword.lower() in title or keyword.lower() in company:
                    filtered.append(job)
                    break
        
        return filtered


def main():
    """Test scraper functionality"""
    logging.basicConfig(level=logging.INFO)
    
    scraper = JobScraper()
    jobs = scraper.scrape_all()
    
    print(f"\nTotal jobs found: {len(jobs)}")
    for job in jobs[:5]:
        print(f"- {job.get('title')} at {job.get('company')} ({job.get('source')})")


if __name__ == '__main__':
    main()