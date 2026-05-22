import re
from typing import List

KEYWORDS = {
    "title": ["security", "sec", "信息安全", "网络安全", "cyber", "risk", "risk management"],
    "company": ["Tencent", "Alibaba", "Huawei", "ByteDance", "JD.com", "Microsoft", "Google"],
    "location": ["北京", "北京/远程", "remote", "线上", "异地"],
}

def _match_keywords(text: str, patterns: List[str]) -> bool:
    """返回是否至少有一个关键字匹配。"""
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False

def score_job(job: dict) -> int:
    """计算 0-3 分：标题、公司、地点各匹配一次得 1 分。"""
    score = 0
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    if _match_keywords(title, KEYWORDS["title"]): score += 1
    if _match_keywords(company, KEYWORDS["company"]): score += 1
    if _match_keywords(location, KEYWORDS["location"]): score += 1
    return score