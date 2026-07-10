"""HTTP client for the Job Monitor API.

Method names mirror the iOS `APIService`: fetch_jobs, fetch_latest_report,
create_job, update_job, delete_job. `build_request` is kept pure and testable
(no network) like the iOS `makeRequest`.
"""

from __future__ import annotations

import requests

from .models import Job

REQUIRED_FIELDS = ["title", "company", "location", "url", "score"]


def validate_job(job: dict) -> list[str]:
    """Mirror the backend `validate_job` rules (api/jobs.py)."""
    errors = []
    for field_name in REQUIRED_FIELDS:
        value = job.get(field_name)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"{field_name} is required")
    if job.get("score") is not None:
        try:
            int(job["score"])
        except (TypeError, ValueError):
            errors.append("score must be an integer")
    return errors


class APIClient:
    def __init__(self, base_url: str, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def build_request(self, path: str, method: str, body: dict | None = None) -> dict:
        """Return the kwargs for a requests call. Pure, no network."""
        req = {"method": method, "url": f"{self.base_url}{path}", "timeout": self.timeout}
        if body is not None:
            req["json"] = body
            req["headers"] = {"Content-Type": "application/json"}
        return req

    def fetch_jobs(self) -> list[Job]:
        resp = requests.request(**self.build_request("/jobs", "GET"))
        resp.raise_for_status()
        return [Job.from_dict(j) for j in resp.json()]

    def fetch_latest_report(self) -> list[Job]:
        """Fetch the latest report and return its jobs (like the iOS list flow)."""
        resp = requests.request(**self.build_request("/latest-report", "GET"))
        resp.raise_for_status()
        data = resp.json()
        return [Job.from_dict(j) for j in data.get("jobs", [])]

    def create_job(self, job: Job) -> Job:
        resp = requests.request(**self.build_request("/jobs", "POST", job.to_dict()))
        resp.raise_for_status()
        return Job.from_dict(resp.json())

    def update_job(self, job: Job) -> Job:
        resp = requests.request(
            **self.build_request(f"/jobs/{job.id}", "PUT", job.to_dict())
        )
        resp.raise_for_status()
        return Job.from_dict(resp.json())

    def delete_job(self, job_id: str) -> None:
        resp = requests.request(**self.build_request(f"/jobs/{job_id}", "DELETE"))
        resp.raise_for_status()
