# Job Monitor — Windows Desktop Client

A Windows desktop client for Monthly Job Monitor, mirroring the iOS app:
browse scraped jobs, filter by score, open a job's URL to apply, and
create / edit / delete jobs via the same backend API.

Built with [PySide6](https://doc.qt.io/qtforpython/) (Qt for Python). It talks
to the same REST API as the iOS app (`APIService.swift`), so no backend changes
are required.

## Features

- **Job list** — loads the latest report from `GET /api/latest-report`.
- **Score filter** — slider filters jobs by `score >= minScore` (same rule as iOS).
- **Apply** — opens the selected job's URL in the default browser (double-click a row).
- **CRUD** — add / edit / delete jobs via `POST` / `PUT` / `DELETE /api/jobs`.
- **Offline cache** — the last successful fetch is cached to `%APPDATA%/JobMonitor/jobs_cache.json`; if the API is unreachable, the client shows the cached jobs.
- **Settings** — configure the API base URL (stored in `%APPDATA%/JobMonitor/settings.json`).

## Run

```bash
cd desktop-win
pip install -r requirements.txt
python -m job_monitor.app
```

Default API base URL: `https://monthly-job-monitor.vercel.app/api` (same as iOS).

### Crawl Now

The **Crawl Now** button runs the repo scraper (`python -m src.scraper.main`)
from the project root — it is not bundled. To use it, run the app from the
source tree with the scraper's environment ready:

```bash
# from the repo root, once
pip install -r requirements.txt
python -m playwright install chromium
# API keys via env vars or config.yaml: TAVILY_API_KEY / EXA_API_KEY / etc.
```

Browsing (list, Top Picks, filter, Apply, CRUD) works with only
`pip install -r desktop-win/requirements.txt` — no scraper env needed, since
data is read from the API.


## Test

```bash
cd desktop-win
pytest
```

Tests cover model parsing (including legacy `salary` → `salaryRange`) and
request construction — no network required.

## Package (optional)

```bash
pip install pyinstaller
pyinstaller JobMonitor.spec
```

Produces `dist/JobMonitor.exe` (standalone, windowed). Note: a packaged exe
covers browsing only; **Crawl Now** won't work in it (the scraper isn't bundled).
For crawling, run from source as above.
