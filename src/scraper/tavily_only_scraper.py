"""Tavily-only scraper for job monitoring - no Playwright needed."""
import json
import os
from src.scraper.config import load_config
from src.scraper.tavily_client import search_jobs, extract_keywords_from_url
from src.scraper.scorer import score_job

def main():
    """Run job search using Tavily API only."""
    cfg = load_config()
    all_jobs = []
    
    print(f"[INFO] Starting Tavily-only job search for {len(cfg.targets)} targets")
    
    for target in cfg.targets:
        # Get URL
        if isinstance(target, dict):
            url = target.get("url") or ""
        else:
            url = getattr(target, "url", "")
        
        if not url:
            continue
            
        # Extract keywords and search
        keywords = extract_keywords_from_url(url)
        print(f"[INFO] Searching for: {keywords} job Beijing")
        
        results = search_jobs(f"{keywords} job Beijing", max_results=5)
        
        for r in results:
            job = {
                "title": r.get("title", "Unknown"),
                "company": "Unknown",
                "location": "Beijing",
                "url": r.get("url", ""),
                "description": r.get("content", "")[:200] if r.get("content") else ""
            }
            # Simple company extraction from title
            if " - " in job["title"]:
                parts = job["title"].split(" - ")
                job["company"] = parts[-1].strip()
            
            job["score"] = score_job(job)
            all_jobs.append(job)
            print(f"[FOUND] {job['title']} @ {job['company']} (score: {job['score']})")
    
    # Save report
    reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports"))
    os.makedirs(reports_dir, exist_ok=True)
    out_path = os.path.join(reports_dir, "jobs.json")
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)
    
    print(f"\n[RESULT] Found {len(all_jobs)} jobs, saved to {out_path}")
    
    # Print high-score jobs
    high_score = [j for j in all_jobs if j.get("score", 0) >= 2]
    if high_score:
        print("\n[HIGH SCORE JOBS]")
        for j in high_score:
            print(f"  ⭐ {j['title']} @ {j['company']}")

if __name__ == "__main__":
    main()