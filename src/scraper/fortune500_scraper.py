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


class Fortune500Scraper:
    def __init__(self):
        """Fortune500.company和Job数据抓取器"""
        # CSV 保存位置（项目根目录下）
        self.csv_path = Path(__file__).parent.parent / "fortune500.csv"

    def scrape_fortune500(self) -> List[Dict]:  # +++
        """从Wikipedia抓取Fortune500完整表格"""
        url = "https://en.wikipedia.org/wiki/Fortune_500"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"[Fortune500Scraper] 网络错误: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="wikitable")
        if not table:
            print("[Fortune500Scraper] 未找到表格")
            return []

        companies = []
        rows = table.find_all("tr")[1:]
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            # 提取公司名称
            company_name = cells[1].get_text(strip=True)
            # 构造官网（简单规则）
            website = f"https://{company_name.replace(' ', '').lower()}.com"
            # 保存必要字段
            companies.append({
                "Company": company_name,
                "Website": website,
                "Keywords": "fortune500, security, engineering"
            })
        return companies

    def generate_career_urls(self, companies: List[Dict]) -> List[Dict]:
        """为每个公司添加职业页面URL"""
        for c in companies:
            website = c.get("Website", "")
            if not website:
                website = f"https://{c.get('Company','').replace(' ','').lower()}.com"
            c["career_url"] = f"{website.rstrip('/')}/careers"
        return companies

    def save_to_csv(self, companies: List[Dict], path: str) -> None:
        """将数据写入CSV文件"""
        keys = ["Company", "Website", "career_url", "Keywords"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for c in companies:
                writer.writerow({
                    "Company": c.get("Company", ""),
                    "Website": c.get("Website", ""),
                    "career_url": c.get("career_url", ""),
                    "Keywords": c.get("Keywords", "")
                })
