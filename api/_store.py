import json
import os
import uuid

# Mutable job store, kept separate from the read-only scraper report (jobs.json)
# so monthly report regeneration never clobbers manually created jobs.
# This is a file-based store: acceptable for local/dev, not durable on Vercel
# serverless. Swap this module's internals for a database behind the same
# functions to move to production persistence.


def _store_path():
    return os.path.join(os.path.dirname(__file__), "../reports/manual_jobs.json")


def _read_all():
    path = _store_path()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    return jobs if isinstance(jobs, list) else []


def _write_all(jobs):
    path = _store_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)


def list_jobs():
    return _read_all()


def create_job(job):
    job = dict(job)
    job["id"] = str(uuid.uuid4())
    jobs = _read_all()
    jobs.append(job)
    _write_all(jobs)
    return job


def update_job(job_id, job):
    jobs = _read_all()
    for i, existing in enumerate(jobs):
        if existing.get("id") == job_id:
            job = dict(job)
            job["id"] = job_id
            jobs[i] = job
            _write_all(jobs)
            return job
    return None


def delete_job(job_id):
    jobs = _read_all()
    remaining = [j for j in jobs if j.get("id") != job_id]
    if len(remaining) == len(jobs):
        return False
    _write_all(remaining)
    return True
