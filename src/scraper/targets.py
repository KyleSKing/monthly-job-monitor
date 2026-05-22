import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List

@dataclass
class Target:
    url: str
    parser: str

def load_fortune500_targets(csv_path: str = "fortune500.csv") -> List[Target]:
    """
    读取 Fortune 500 CSV 文件并生成目标列表。
    CSV 必须包含至少两列：Company, Website
    可选列：Keywords（用于后续关键词匹配）
    每一行会根据 Website 拼接一个搜索 URL（示例实现）。
    """
    targets: List[Target] = []
    csv_file = Path(csv_path)
    if not csv_file.is_file():
        return targets  # 如果文件不存在，静默返回空列表

    with csv_file.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            company = row.get("Company", "").strip()
            website = row.get("Website", "").strip()
            keywords = row.get("Keywords", "").strip()
            if not website:
                continue

            # 简单示例：在公司官方职业页面后拼接搜索词
            search_url = f"{website.rstrip('/')}/search?keywords=information%20security"
            # 统一使用 generic 解析器
            targets.append(Target(url=search_url, parser="generic"))
    return targets