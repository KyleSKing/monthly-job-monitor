"""Tests for offline job cache (isolated APPDATA, no network)."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from job_monitor import cache  # noqa: E402
from job_monitor.models import Job  # noqa: E402


def _sample():
    return [
        Job(title="Engineer", company="Acme", location="Beijing",
            url="https://x", score=5, id="a1"),
        Job(title="Analyst", company="Globex", location="Shanghai",
            url="https://y", score=8, id="b2", salary_range="30-50K"),
    ]


def test_load_missing_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert cache.load_jobs() == []


def test_save_then_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    cache.save_jobs(_sample())
    loaded = cache.load_jobs()
    assert [j.id for j in loaded] == ["a1", "b2"]
    assert loaded[1].salary_range == "30-50K"
    assert loaded[0].score == 5


def test_load_corrupt_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    cache.save_jobs(_sample())
    with open(cache._cache_path(), "w", encoding="utf-8") as f:
        f.write("{ not json")
    assert cache.load_jobs() == []
