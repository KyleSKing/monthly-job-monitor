import re
from typing import List

KEYWORDS = {
    "title": ["security", "sec", "信息安全", "网络安全", "cyber", "risk", "risk management"],
    "company": ["腾讯", "阿里巴巴", "华为", "字节跳动", "京东", "Microsoft", "Google"],
    "location": ["北京", "北京/远程", "remote", "线上", "异地"],
}

def _match_keywords(text: str, patterns: List[str]) -> int:
    hits = 0
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE):
            hits += 1
    return hits

def score_job(job: dict) -> int:
    """计算 0-3 分：标题、公司、地点各匹配一次得 1 分。"""
    score = 0
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    score += _match_keywords(title, KEYWORDS["title"])
    score += _match_keywords(company, KEYWORDS["company"])
    score += _match_keywords(location, KEYWORDS["location"])
    return min(score, 3)