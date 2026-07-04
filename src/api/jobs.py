import json
import os
from http.server import BaseHTTPRequestHandler


def get_all_jobs():
    """Get all jobs from the latest report"""
    report = get_latest_report()
    if report is None:
        return []
    return report.get("jobs", [])


def get_latest_report():
    """Get the latest monthly job report JSON"""
    # Look for the latest report in output directory
    root_dir = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(root_dir, "../../output")
    if not os.path.exists(output_dir):
        return None

    # Find the latest json file
    json_files = []
    for f in os.listdir(output_dir):
        if f.endswith(".json") and f.startswith("report_"):
            json_files.append(os.path.join(output_dir, f))

    if not json_files:
        return None

    # Sort by modification time, newest first
    json_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    latest_file = json_files[0]

    with open(latest_file, "r", encoding="utf-8") as f:
        return json.load(f)


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
