import concurrent.futures
import json
import os
from .config import load_config, ScraperConfig
from .tavily_client import fallback_fetch
from .playwright_scraper import PlaywrightScraper
from .parsers import REGISTERED_PARSERS
from .scorer import score_job
from .email_sender import send_email
from ._exceptions import ScraperError


def process_target(target, scraper):
    """单个目标的完整处理流程：抓取 → 解析 → 打分 → 返回"""
    # 兼容 dict 与 Target 对象两种传入方式
    if isinstance(target, dict):
        url = target.get("url") or target.get("search_url") or ""
        parser_name = target.get("parser", "generic")
    else:
        url = getattr(target, "url", None)
        parser_name = getattr(target, "parser", "generic")

    if not url:
        raise ScraperError("目标缺少 URL")

    try:
        html = scraper.fetch(url)
    except ScraperError as e:
        # 使用 Tavily 搜索获取候选 URL
        print(f"[INFO] 使用 Tavily 搜索替代 {url}")
        candidate_urls = fallback_fetch(url)
        if not candidate_urls:
            raise ScraperError(f"无法获取 {url} 的页面，且 Tavily 搜索无结果") from e
        # 尝试第一个候选 URL
        html = scraper.fetch(candidate_urls[0])

    parser_fn = REGISTERED_PARSERS.get(parser_name, REGISTERED_PARSERS.get("generic"))
    job = parser_fn(html)
job['Score'] = score_job(job)
        del job['score']  # Ensure only "Score" key remains
    return job


def run():
    # 加载配置（自动会拉取 Fortune 500 目标并更新 cfg.targets）
    cfg: ScraperConfig = load_config()

    # 初始化核心组件
    scraper = PlaywrightScraper()

    # 并行抓取所有目标
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

    # 保存报告
    reports_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "reports")
    )
    os.makedirs(reports_dir, exist_ok=True)
    out_path = os.path.join(reports_dir, "jobs.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    # 发送高分（score == 3）职位邮件
    high_score = [j for j in all_jobs if j.get("score") == 3]
    if high_score:
        body = "\n".join(
            f"{j['title']} @ {j['company']} ({j['location']})"
            for j in high_score
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


if __name__ == "__main__":
    try:
        run()
    except ScraperError as exc:
        print(f"[ERROR] {exc}")