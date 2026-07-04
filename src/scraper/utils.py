import re
import requests
from bs4 import BeautifulSoup

SALARY_RE = re.compile(
    r"(?i)(\d{1,3}\.?\d*)\s*(k|K|w|W|\u5343|\u4e07|\u4e07\u4eba\u6c11\u5e01|\u4e07\u5546)\s*(/\s*(\w+|\u6bcf\u6708|\u5e74|month|year|¥|yuan))?"
)


def fetch_salary_range(url: str) -> str:
    """Returns the first found salary range string or 'N/A' if not found."""
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        matches = SALARY_RE.findall(text)
        if matches:
            # 只返回第一个匹配，格式化
            amount, unit, _ = matches[0]
            return f"{amount}{unit.strip().upper()}"
        else:
            return "N/A"
    except Exception as e:
        return "N/A"
