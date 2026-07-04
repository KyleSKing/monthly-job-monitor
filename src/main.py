#!/usr/bin/env python3
"""
Monthly Job Monitor — Main Entry Point
3-tier scraper: Exa+Jina → Serper+Firecrawl → Tavily
"""
import logging
import sys
import os

# Ensure the project root is on sys.path so package imports work
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.scraper.main import TieredScraper
from src.scraper.scorer import score_job
from src.scraper.email_sender import send_email

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_report(jobs: list, output_dir: str = "reports") -> str:
    """Generate markdown report from job listings."""
    from datetime import datetime
    from pathlib import Path
    import re

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    filename = f"recruitment_report_{datetime.now().strftime('%Y-%m')}.md"
    filepath = out / filename

    # ── 福利提取函数 ──
    BENEFIT_KEYWORDS = {
        "💰薪资": [
            "stock",
            "option",
            "rsu",
            "bonus",
            "奖金",
            "股权",
            "期权",
            "分红",
            "年薪",
            "月薪",
            "薪资",
            "工资",
            "13薪",
            "14薪",
            "15薪",
            "16薪",
        ],
        "🏥保险": [
            "五险一金",
            "补充医疗",
            "商业保险",
            "health insurance",
            "medical",
            "保险",
            "公积金",
            "housing fund",
        ],
        "🏠远程": [
            "remote",
            "远程",
            "work from home",
            "居家",
            "flexible",
            "弹性工作",
            "弹性",
            "线上",
            "异地",
        ],
        "🍱福利": [
            "免费午餐",
            "下午茶",
            "gym",
            "健身房",
            "餐补",
            "交通补",
            "补贴",
            "allowance",
            "paid leave",
            "年假",
            "带薪",
        ],
        "📈成长": [
            "training",
            "培训",
            "learning",
            "学习",
            "career growth",
            "晋升",
            "发展",
            "education",
            "深造",
        ],
    }

    def _extract_benefits(desc: str, title: str, salary: str) -> str:
        text = (desc + " " + title).lower()
        found = []
        if salary and salary not in ("N/A", ""):
            found.append(f"💰{salary[:30]}")
        for icon, kws in BENEFIT_KEYWORDS.items():
            for kw in kws:
                if kw.lower() in text:
                    found.append(icon)
                    break
        return " ".join(found) if found else "—"

    # ── 评分 → 星星 ──
    def _score_stars(s):
        return "⭐" * s if s else "—"

    md = f"# 📋 招聘监控报告\n\n"
    md += f"_生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n"
    md += f"**职位总数: {len(jobs)}**\n\n"

    md += "| # | 职位 | 公司 | 地点 | 薪资/福利 | 评分 |\n"
    md += "|---|------|------|------|-----------|------|\n"
    for rank, job in enumerate(jobs[:30], 1):
        title = job.get("title", "N/A")
        company = job.get("company", "N/A")
        loc = job.get("location", "N/A")
        salary = job.get("salary", "N/A")
        desc = job.get("description", "") or ""
        score = job.get("Score", 0)
        benefits = _extract_benefits(desc, title, salary)
        md += (
            f"| {rank} | [{title}]({job.get('url','#')}) "
            f"| {company} | {loc} "
            f"| {benefits} "
            f"| {_score_stars(score)} |\n"
        )

    # ── 高薪/高福利岗位特别标注 ──
    high_value = [j for j in jobs if j.get("Score", 0) >= 7]
    if high_value:
        md += "\n\n## 🔥 高价值岗位 (评分≥7)\n\n"
        for j in high_value:
            title = j.get("title", "N/A")
            company = j.get("company", "N/A")
            salary = j.get("salary", "N/A")
            md += f"- [{title}]({j.get('url','#')}) — {company} | {salary}\n"

    # ── 评分分布 ──
    from collections import Counter

    dist = Counter(j.get("Score", 0) for j in jobs)
    md += "\n\n## 📊 评分分布\n\n"
    for k in sorted(dist.keys(), reverse=True):
        bar = "█" * min(dist[k] // 10, 50)
        pct = dist[k] / len(jobs) * 100
        md += f"**{k}分**: {bar} {dist[k]}条 ({pct:.1f}%)\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)

    logger.info(f"Report saved to {filepath}")
    return str(filepath)


def main():
    logger.info("Starting Monthly Job Monitor (3-Tier Scraper)")

    scraper = TieredScraper()
    jobs = scraper.scrape_all()

    logger.info(f"Total jobs found: {len(jobs)}")

    if not jobs:
        logger.warning("No jobs found. Check API keys and internet connection.")
        return

    # Generate reports
    report_path = generate_report(jobs)
    logger.info(f"Report generated: {report_path}")

    # Print top 5 summary
    print(f"\n{'='*60}")
    print(f"Monthly Job Monitor — Results")
    print(f"{'='*60}")
    print(f"Total jobs: {len(jobs)}")
    print(f"Report: {report_path}")
    print(f"\nTop 5 jobs:")
    for rank, job in enumerate(jobs[:5], 1):
        print(
            f"  {rank}. {job.get('title','N/A')} — {job.get('company','N/A')} [{job.get('source','N/A')}]"
        )


if __name__ == "__main__":
    main()
