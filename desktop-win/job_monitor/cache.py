"""Local job cache for offline fallback.

Persists the last successfully fetched jobs so the client can display them
when the API is unreachable.
"""

from __future__ import annotations

import json
import os

from .models import Job


def _cache_path() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "JobMonitor", "jobs_cache.json")


def save_jobs(jobs: list[Job]) -> None:
    path = _cache_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([j.to_dict() for j in jobs], f, ensure_ascii=False, indent=2)


def load_jobs() -> list[Job]:
    path = _cache_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return [Job.from_dict(j) for j in data]
