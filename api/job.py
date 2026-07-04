import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from _store import delete_job, update_job
from jobs import _map_job, validate_job


def _job_id_from_path(path):
    """Extract the job id from /api/jobs/{id} or a ?id={id} query param."""
    parsed = urlparse(path)
    query_id = parse_qs(parsed.query).get("id", [None])[0]
    if query_id:
        return query_id
    parts = [p for p in parsed.path.split("/") if p]
    if parts:
        last = parts[-1]
        if last not in ("job", "jobs") and not last.endswith(".py"):
            return last
    return None


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_PUT(self):
        job_id = _job_id_from_path(self.path)
        if not job_id:
            self._respond(400, {"errors": ["job id is required"]})
            return

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

        updated = update_job(job_id, _map_job(body))
        if updated is None:
            self._respond(404, {"errors": ["job not found"]})
            return
        self._respond(200, updated)

    def do_DELETE(self):
        job_id = _job_id_from_path(self.path)
        if not job_id:
            self._respond(400, {"errors": ["job id is required"]})
            return

        if not delete_job(job_id):
            self._respond(404, {"errors": ["job not found"]})
            return

        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _respond(self, status, payload):
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))
