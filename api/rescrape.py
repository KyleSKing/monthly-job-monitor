import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler

# Manual re-scrape endpoint.
# The real scraper needs Playwright + external APIs + minutes of runtime, which
# Vercel serverless cannot host. So instead we trigger the existing GitHub
# Actions workflow (monthly-scrape.yml) via workflow_dispatch. It runs the
# scrape and commits reports/jobs.json back to the repo, which Vercel serves.

WORKFLOW_FILE = "monthly-scrape.yml"


def trigger_workflow(token, repo, ref="main"):
    """POST a workflow_dispatch to GitHub Actions.

    Returns (status_code, payload_dict). Requires a repo-scoped token in the
    GITHUB_TOKEN env var and the target repo in GITHUB_REPO (owner/name).
    """
    if not token or not repo:
        return 501, {
            "error": "re-scrape not configured: set GITHUB_TOKEN and GITHUB_REPO"
        }

    url = f"https://api.github.com/repos/{repo}/actions/workflows/{WORKFLOW_FILE}/dispatches"
    body = json.dumps({"ref": ref}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            # GitHub returns 204 No Content on success
            if resp.status == 204:
                return 202, {"status": "triggered", "workflow": WORKFLOW_FILE}
            return resp.status, {"status": "unexpected", "code": resp.status}
    except urllib.error.HTTPError as e:
        return e.code, {"error": f"GitHub API error: {e.code}"}
    except urllib.error.URLError as e:
        return 502, {"error": f"cannot reach GitHub: {e.reason}"}


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        token = os.getenv("GITHUB_TOKEN", "")
        repo = os.getenv("GITHUB_REPO", "")
        ref = os.getenv("GITHUB_REF_NAME", "main")

        status, payload = trigger_workflow(token, repo, ref)
        self._respond(status, payload)

    def _respond(self, status, payload):
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))
