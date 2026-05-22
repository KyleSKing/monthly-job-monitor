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
    # 1️⃣ 加载配置（自动会拉取 Fortune 500 目标并更新 cfg.targets）
    cfg: ScraperConfig = load_config()

    # 2️⃣ 初始化核心组件
    tavily = TavilyClient(cfg)          # 目前未使用，可在将来加入关键字预搜索
    scraper = PlaywrightScraper()

    # 3️⃣ 并行抓取所有目标
    all_jobs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(process_target, target, scraper): target
            for target in cfg.targets
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                job = future.result()
                all_jobs.append(job)
            except ScraperError as e:
                print(f"[WARN] 处理目标时出错: {e}")

    # 4️⃣ 保存报告
    reports_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "reports")
    )
    os.makedirs(reports_dir, exist_ok=True)
    out_path = os.path.join(reports_dir, "jobs.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    # 5️⃣ 发送高分（score == 3）职位邮件
    high_score = [j for j in all_jobs if j.get("score") == 3]
    if high_score:
        body = "\n".join(
            f"{j['title']} @ {j['company']} ({j['location']})" for j in high_score
        )
        send_email(
            email_cfg={
                "sender": "no-reply@example.com",
                "receiver": "you@example.com",
                "host": "smtp.example.com",
            },
            subject="【Monthly Job Monitor】高分职位报告",
            body=body,
        )

def process_target(target, scraper):
    """单个目标的完整处理流程：抓取 → 解析 → 打分 → 返回"""
    html = scraper.fetch(target.url)
    parser_fn = REGISTERED_PARSERS.get(target.parser, REGISTERED_PARSERS.get("generic"))
    job = parser_fn(html)
    job["score"] = score_job(job)
    return job

if __name__ == "__main__":
    try:
        run()
    except ScraperError as exc:
        print(f"[ERROR] {exc}")