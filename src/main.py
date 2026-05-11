#!/usr/bin/env python3
"""
Monthly Job Monitor - Main Entry Point
Scrapes job listings and sends monthly recruitment report
"""

import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import JobScraper
from email_sender import EmailSender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_report(jobs: list, output_dir: str = "reports") -> str:
    """Generate markdown report file"""
    Path(output_dir).mkdir(exist_ok=True)
    
    month = datetime.now().strftime('%Y-%m')
    filename = f"{output_dir}/recruitment_report_{month}.md"
    
    lines = [
        f"# Monthly Recruitment Report - {month}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total Jobs:** {len(jobs)}",
        "",
        "## Summary",
        "",
        f"- Indeed: {len([j for j in jobs if j.get('source') == 'Indeed'])} jobs",
        f"- LinkedIn: {len([j for j in jobs if j.get('source') == 'LinkedIn'])} jobs",
        "",
        "## Job Listings",
        "",
        "| Title | Company | Location | Source | Salary |",
        "|-------|---------|----------|--------|--------|",
    ]
    
    for job in jobs:
        title = job.get('title', 'N/A')
        company = job.get('company', 'N/A')
        location = job.get('location', 'N/A')
        source = job.get('source', 'N/A')
        salary = job.get('salary', 'N/A')
        url = job.get('url', '#')
        
        lines.append(f"| [{title}]({url}) | {company} | {location} | {source} | {salary} |")
    
    content = "\n".join(lines)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Report saved to: {filename}")
    return filename


def main():
    """Main execution function"""
    logger.info("=" * 50)
    logger.info("Monthly Job Monitor Started")
    logger.info("=" * 50)
    
    # Configuration file path
    config_path = os.environ.get('CONFIG_PATH', 'config.yaml')
    
    # Check if config exists
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        logger.info("Please create config.yaml with email and scraper settings")
        sys.exit(1)
    
    try:
        # Step 1: Scrape job listings
        logger.info("[1/3] Initializing job scraper...")
        scraper = JobScraper(config_path)
        
        logger.info("[2/3] Scraping job listings...")
        jobs = scraper.scrape_all()
        
        if not jobs:
            logger.warning("No jobs found!")
            # Still send report with empty list
            jobs = []
        
        logger.info(f"Found {len(jobs)} jobs")
        
        # Step 2: Generate report file
        logger.info("[3/3] Generating report...")
        report_path = generate_report(jobs)
        
        # Step 3: Send email
        logger.info("Sending email notification...")
        sender = EmailSender(config_path)
        
        success = sender.send_report(jobs)
        
        if success:
            logger.info("✅ Monthly job monitor completed successfully!")
        else:
            logger.error("❌ Failed to send email")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()