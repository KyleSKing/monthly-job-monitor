"""Tests for the API client request building and model parsing (no network)."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from job_monitor.api_client import APIClient, validate_job  # noqa: E402
from job_monitor.models import Job  # noqa: E402

BASE = "https://example.com/api"


def test_job_from_dict_maps_legacy_salary():
    job = Job.from_dict(
        {
            "id": "abc",
            "title": "Engineer",
            "company": "Acme",
            "location": "Beijing",
            "url": "https://x",
            "score": "3",
            "salary": "40-65K",
        }
    )
    assert job.score == 3
    assert job.salary_range == "40-65K"


def test_job_to_dict_normalizes_salary_range():
    job = Job(
        title="Engineer",
        company="Acme",
        location="Beijing",
        url="https://x",
        score=3,
        salary_range="40-65K",
    )
    payload = job.to_dict()
    assert payload["salaryRange"] == "40-65K"
    assert "salary" not in payload


def test_build_request_get():
    client = APIClient(BASE)
    req = client.build_request("/jobs", "GET")
    assert req["method"] == "GET"
    assert req["url"] == f"{BASE}/jobs"
    assert "json" not in req


def test_build_request_put_has_body_and_headers():
    client = APIClient(BASE)
    job = Job(title="T", company="C", location="L", url="https://x", score=1, id="42")
    req = client.build_request(f"/jobs/{job.id}", "PUT", job.to_dict())
    assert req["method"] == "PUT"
    assert req["url"] == f"{BASE}/jobs/42"
    assert req["json"]["title"] == "T"
    assert req["headers"]["Content-Type"] == "application/json"


def test_base_url_trailing_slash_stripped():
    client = APIClient(BASE + "/")
    assert client.build_request("/jobs", "GET")["url"] == f"{BASE}/jobs"


def test_validate_job_flags_missing_fields():
    errors = validate_job({"title": "T"})
    assert any("company is required" in e for e in errors)


def test_validate_job_passes_valid():
    errors = validate_job(
        {"title": "T", "company": "C", "location": "L", "url": "u", "score": 2}
    )
    assert errors == []


def test_fetch_calls_requests_request_without_method_clash(monkeypatch):
    """Regression: fetch used requests.get(**req) where req also had 'method',
    raising 'multiple values for method'. Ensure requests.request is used."""
    captured = {}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"jobs": [{"title": "T", "company": "C", "location": "L",
                              "url": "u", "score": 1}]}

    def fake_request(**kwargs):
        captured.update(kwargs)
        return FakeResp()

    import job_monitor.api_client as mod

    monkeypatch.setattr(mod.requests, "request", fake_request)
    jobs = APIClient(BASE).fetch_latest_report()
    assert captured["method"] == "GET"
    assert len(jobs) == 1

