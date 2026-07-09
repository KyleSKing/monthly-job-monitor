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
- **Settings** — configure the API base URL (stored in `%APPDATA%/JobMonitor/settings.json`).

## Run

```bash
cd desktop-win
pip install -r requirements.txt
python -m job_monitor.app
```

Default API base URL: `https://monthly-job-monitor.vercel.app/api` (same as iOS).

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
pyinstaller --onefile --windowed --name JobMonitor job_monitor/app.py
```

Produces `dist/JobMonitor.exe`.
