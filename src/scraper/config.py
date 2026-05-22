import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Any
import os

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.yaml"))

@dataclass
class Target:
    name: str
    url: str
    parser: str  # e.g. "linkedin", "zhaopin", "51job", "generic"

@dataclass
class ScraperConfig:
    tavily_api_key: str
    use_tavily: bool = True
    request_delay: float = 1.0
    timeout: int = 30
    max_results: int = 20
    targets: List[Target] = field(default_factory=list)

def load_config(path: str = CONFIG_PATH) -> ScraperConfig:
    """加载项目根目录的 `config.yaml` 并返回 dataclass 实例。"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"config.yaml not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # 兼容旧结构：raw 里可能直接是 dict 或者嵌套在 `scraper:` 键下
    cfg = raw.get("scraper", raw)

    targets = [
        Target(**t) for t in cfg.get("targets", [])
    ]

    return ScraperConfig(
        tavily_api_key=cfg.get("tavily_api_key", "[REDACTED]"),
        use_tavily=cfg.get("use_tavily", True),
        request_delay=cfg.get("request_delay", 1.0),
        timeout=cfg.get("timeout", 30),
        max_results=cfg.get("max_results", 20),
        targets=targets,
    )