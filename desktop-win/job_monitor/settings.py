"""Local settings persistence (API base URL)."""

from __future__ import annotations

import json
import os

DEFAULT_BASE_URL = "https://monthly-job-monitor.vercel.app/api"


def _settings_path() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "JobMonitor", "settings.json")


def load_base_url() -> str:
    path = _settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            url = data.get("baseURL")
            if isinstance(url, str) and url.strip():
                return url.strip()
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_BASE_URL


def save_base_url(base_url: str) -> None:
    path = _settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"baseURL": base_url.strip()}, f, ensure_ascii=False, indent=2)
