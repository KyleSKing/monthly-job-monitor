import csv
import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .targets import Target


@dataclass
class ScraperConfig:
    targets: List[Target]
    tavily_api_key: str
    use_tavily: bool
    request_delay: float
    timeout: int
    max_results: int
    # New Tier 1 & 2 config
    exa_api_key: str = ""
    jina_api_key: str = ""
    serper_api_key: str = ""
    serper_endpoint: str = ""
    firecrawl_token: str = ""


def _get_key(data: dict, key: str, env_var: str) -> str:
    """Get key from config file; if empty, fall back to env var."""
    val = data.get(key, "")
    return val if val else os.getenv(env_var, "")


def load_config(config_path: str = "config.yaml") -> ScraperConfig:
    """
    Load config from YAML file with env var fallbacks for API keys.
    """
    cfg_path = Path(config_path)
    if not cfg_path.is_file():
        # Try project root
        cfg_path = Path(__file__).parent.parent.parent / config_path
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    cfg = ScraperConfig(
        targets=data.get("targets", []),
        tavily_api_key=_get_key(data, "tavily_api_key", "TAVILY_API_KEY"),
        use_tavily=data.get("use_tavily", True),
        request_delay=data.get("request_delay", 1.0),
        timeout=data.get("timeout", 30),
        max_results=data.get("max_results", 50),
        exa_api_key=_get_key(data, "exa_api_key", "EXA_API_KEY"),
        jina_api_key=_get_key(data, "jina_api_key", "JINA_API_KEY"),
        serper_api_key=_get_key(data, "serper_api_key", "SERPER_API_KEY"),
        serper_endpoint=_get_key(data, "serper_endpoint", "SERPER_ENDPOINT"),
        firecrawl_token=_get_key(data, "firecrawl_token", "FIRECRAWL_TOKEN"),
    )

    # Auto-append fortune500 targets if file exists
    fortune_targets = []
    fortune_csv = Path("fortune500.csv")
    if fortune_csv.is_file():
        fortune_targets = load_fortune500_targets("fortune500.csv")
    cfg.targets = cfg.targets + fortune_targets

    return cfg


def load_fortune500_targets(csv_path: str = "fortune500.csv") -> List[Target]:
    """Read Fortune 500 CSV and generate target list."""
    targets: List[Target] = []
    csv_file = Path(csv_path)
    if not csv_file.is_file():
        return targets

    with csv_file.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            company = row.get("Company", "").strip()
            website = row.get("Website", "").strip()
            keywords = row.get("Keywords", "").strip()
            if not website:
                continue

            search_url = f"{website.rstrip('/')}/search?keywords=information%20security"
            targets.append(Target(url=search_url, parser="generic"))
    return targets