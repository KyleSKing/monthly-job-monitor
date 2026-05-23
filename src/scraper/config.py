import csv
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .fortune500_scraper import Fortune500Scraper
from .targets import Target


@dataclass
class ScraperConfig:
    targets: List[Target]
    tavily_api_key: str
    use_tavily: bool
    request_delay: float
    timeout: int
    max_results: int


def load_config(config_path: str = "config.yaml") -> ScraperConfig:
    """
    加载配置并自动生成 Fortune 500 目标列表。
    """
    cfg_path = Path(config_path)
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    cfg = ScraperConfig(
        targets=data.get("targets", []),
        tavily_api_key=data.get("tavily_api_key", ""),
        use_tavily=data.get("use_tavily", False),
        request_delay=data.get("request_delay", 1.0),
        timeout=data.get("timeout", 30),
        max_results=data.get("max_results", 50),
    )

    # If fortune500.csv is missing, skip auto-fetch.
    fortune_targets = []
    fortune_csv = Path("fortune500.csv")
    if fortune_csv.is_file():
        fortune_targets = load_fortune500_targets("fortune500.csv")
    cfg.targets = cfg.targets + fortune_targets


    return cfg


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
            # 你可以自定义更智能的 URL 生成策略
            search_url = f"{website.rstrip('/')}/search?keywords=information%20security"
            # 若提供了关键词列表，可在解析器注册表中加入自定义解析器
            # 本例中统一使用 generic 解析器
            targets.append(Target(url=search_url, parser="generic"))
    return targets