import json
import os
import uuid
from http.server import BaseHTTPRequestHandler

from _store import create_job, list_jobs

REQUIRED_FIELDS = ["title", "company", "location", "url", "score"]


def validate_job(job):
    """Return a list of validation error messages (empty if valid)."""
    errors = []
    for field in REQUIRED_FIELDS:
        value = job.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"{field} is required")
    if "score" in job and job.get("score") is not None:
        try:
            int(job["score"])
        except (TypeError, ValueError):
            errors.append("score must be an integer")
    return errors


def _jobs_path():
    return os.path.join(os.path.dirname(__file__), "../reports/jobs.json")


def _coerce_score(job):
    value = job.get("score", job.get("Score", job.get("tavily_relevance_score", 0)))
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _job_id(job):
    key = "|".join(
        [
            str(job.get("url", "")),
            str(job.get("title", "")),
            str(job.get("company", "")),
        ]
    )
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


def _map_job(job):
    return {
        "id": job.get("id") or _job_id(job),
        "title": job.get("title") or "Untitled",
        "company": job.get("company") or "Unknown",
        "location": job.get("location") or "Unknown",
        "url": job.get("url") or "",
        "score": _coerce_score(job),
        "summary": job.get("summary") or job.get("description") or "",
        "source": job.get("source") or "Job Monitor",
        "publishedDate": job.get("publishedDate") or job.get("published_date"),
        "salaryRange": job.get("salaryRange")
        or job.get("salary_range")
        or job.get("salary"),
    }


def get_all_jobs():
    """Get read-only report jobs plus mutable store jobs, in the iOS API shape."""
    path = _jobs_path()
    report_jobs = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        if isinstance(jobs, list):
            report_jobs = jobs

    return [_map_job(job) for job in report_jobs] + [
        _map_job(job) for job in list_jobs()
    ]


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        jobs = get_all_jobs()
        self.wfile.write(json.dumps(jobs).encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            self._respond(400, {"errors": ["invalid JSON body"]})
            return

        errors = validate_job(body)
        if errors:
            self._respond(400, {"errors": errors})
            return

        created = create_job(_map_job(body))
        self._respond(201, created)

    def _respond(self, status, payload):
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))
