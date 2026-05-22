import csv
import re
import sys
from pathlib import Path
from typing import List, Dict

from bs4 import BeautifulSoup
import requests

KEYWORDS = {
    "title": ["security", "sec", "信息安全", "网络安全", "cyber", "risk", "risk management"],
    "company": ["Tencent", "Alibaba", "Huawei", "ByteDance", "JD.com", "Microsoft", "Google"],
    "location": ["北京", "北京/远程", "remote", "线上", "异地"],
}


def _match_keywords(text: str, patterns: List[str]) -> bool:
    """Return True if any pattern matches (case‑insensitive)."""
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def score_job(job: Dict) -> int:
    """Score a job dict (0‑3)."""
    score = 0
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")

    if _match_keywords(title, KEYWORDS["title"]):
        score += 1
    if _match_keywords(company, KEYWORDS["company"]):
        score += 1
    if _match_keywords(location, KEYWORDS["location"]):
        score += 1
    return score


def load_fortune500(csv_path: Path) -> List[Dict]:
    """Read Fortune 500 CSV and return list of job dicts."""
    jobs = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            jobs.append(
                {
                    "title": row.get("Title", ""),
                    "company": row.get("Company", ""),
                    "location": row.get("Location", ""),
                }
            )
    return jobs