import json
import os
from .config import load_config, ScraperConfig
from .tavily_client import TavilyClient
from .playwright_scraper import PlaywrightScraper
from .parsers import REGISTERED_PARSERS
from .scorer import score_job
from .email_sender import send_email
from ._exceptions import ScraperError

def run():
    cfg: ScraperConfig = load_config()
    tavily = TavilyClient(cfg)
    scraper = PlaywrightScraper()

    all_jobs = []

    for target in cfg.targets:
        html = scraper.fetch(target.url)
        parser_fn = REGISTERED_PARSERS.get(target.parser, REGISTERED_PARSERS.get("generic"))
        job = parser_fn(html)
        job["score"] = score_job(job)
        all_jobs.append(job)

    reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports"))
    os.makedirs(reports_dir, exist_ok=True)
    out_path = os.path.join(reports_dir, "jobs.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    high_score = [j for j in all_jobs if j["score"] == 3]
    if high_score:
        body = "\n".join([f"{j['title']} @ {j['company']} ({j['location']})" for j in high_score])
        send_email(
            email_cfg={"sender": "no-reply@example.com", "receiver": "you@example.com", "host": "smtp.example.com"},
            subject="【Monthly Job Monitor】高分职位报告",
            body=body,
        )

if __name__ == "__main__":
    try:
        run()
    except ScraperError as exc:
        print(f"[ERROR] {exc}")