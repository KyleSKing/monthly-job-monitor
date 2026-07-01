import json
import os
import uuid
from http.server import BaseHTTPRequestHandler


def _jobs_path():
    return os.path.join(os.path.dirname(__file__), "../reports/jobs.json")


def _coerce_score(job):
    value = job.get("score", job.get("Score", job.get("tavily_relevance_score", 0)))
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _job_id(job):
    key = "|".join([
        str(job.get("url", "")),
        str(job.get("title", "")),
        str(job.get("company", "")),
    ])
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
        "salaryRange": job.get("salaryRange") or job.get("salary_range") or job.get("salary"),
    }


def get_all_jobs():
    """Get all jobs from reports/jobs.json in the iOS API shape."""
    path = _jobs_path()
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    if not isinstance(jobs, list):
        return []

    return [_map_job(job) for job in jobs]


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        jobs = get_all_jobs()
        self.wfile.write(json.dumps(jobs).encode("utf-8"))
