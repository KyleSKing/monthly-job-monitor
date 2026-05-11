# Heartbeat Configuration

```markdown
# Monthly Job Monitor - Heartbeat Schedule
# Runs on the 1st of every month at 8:00 AM

schedule: "0 8 1 * *"
enabled: true

tasks:
  - name: monthly-job-scrape
    description: Scrape job listings and send recruitment report
    command: python src/main.py
```

## Schedule Format (cron)
- Minute: 0
- Hour: 8 (8:00 AM)
- Day of Month: 1 (1st)
- Month: * (every month)
- Day of Week: * (any day)

**Result**: Runs at 8:00 AM on the 1st of every month