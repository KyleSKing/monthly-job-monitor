# Monthly Job Monitor

🤖 Automated job scraping and recruitment report delivery system

## Features

- 📅 **Monthly Scheduling** - Automatically runs on the 1st of every month
- 🌐 **Multi-Source Scraping** - Scrapes job listings from LinkedIn, Indeed, and other platforms
- 📧 **Email Delivery** - Sends formatted recruitment reports to `bin.deng2@boeing.com`
- 📊 **Report Generation** - Creates markdown and HTML reports with job listings
- 🔄 **GitHub Actions** - Backup automation using GitHub CI/CD

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/KyleSKing/monthly-job-monitor.git
cd monthly-job-monitor
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Settings

Edit `config.yaml` with your email and scraper settings:

```yaml
email:
  to: bin.deng2@boeing.com
  from: your-email@gmail.com
  smtp_server: smtp.gmail.com
  smtp_port: 587
  username: your-email@gmail.com
  password: your-app-password  # Use app password, not login password
```

### 4. Run Manually

```bash
cd src
python main.py
```

## Configuration

### Email Settings

| Setting | Description |
|---------|-------------|
| `to` | Recipient email address |
| `from` | Sender email address |
| `smtp_server` | SMTP server (e.g., smtp.gmail.com) |
| `smtp_port` | SMTP port (usually 587 for TLS) |
| `username` | SMTP username |
| `password` | SMTP password (use app password) |

### Scraper Settings

Configure target job websites in `config.yaml`:

```yaml
scraper:
  targets:
    - name: "LinkedIn Jobs"
      enabled: true
      url: "https://www.linkedin.com/jobs/search/"
      keywords:
        - "software engineer"
        - "data scientist"
```

## Automation

### OpenClaw Heartbeat (Primary)

The project uses OpenClaw's HEARTBEAT.md for scheduling:

```markdown
# HEARTBEAT.md
schedule: "0 8 1 * *"  # Monthly on 1st at 8:00 AM
```

### GitHub Actions (Backup)

GitHub Actions provides backup automation:

```yaml
# .github/workflows/monthly-scrape.yml
on:
  schedule:
    - cron: '0 8 1 * *'  # Monthly on 1st at 8:00 AM UTC
  workflow_dispatch:    # Manual trigger
```

## Project Structure

```
monthly-job-monitor/
├── src/
│   ├── main.py          # Main entry point
│   ├── scraper.py       # Job scraping module
│   └── email_sender.py  # Email sending module
├── config.yaml          # Configuration file
├── requirements.txt    # Python dependencies
├── reports/            # Generated reports
├── .github/
│   └── workflows/
│       └── monthly-scrape.yml  # GitHub Actions
└── HEARTBEAT.md        # OpenClaw scheduling
```

## Output

### Email Report Format

The email report includes:
- Total job count
- Job title
- Company name
- Location
- Salary range (if available)
- Job URL link

### Report Files

Reports are saved to `reports/` directory:
- `recruitment_report_2026-01.md`
- `recruitment_report_2026-02.md`
- ...

## Troubleshooting

### Email Not Sending

1. **Check app password** - Gmail requires app passwords, not login passwords
2. **Enable IMAP** - Go to Gmail Settings > Security > Enable 2FA > Generate app password
3. **Check spam folder** - Email might be in spam

### No Jobs Found

1. Check internet connection
2. Verify target URLs in config.yaml
3. Some sites may block scraping - consider using official APIs

### GitHub Actions Failed

1. Check workflow logs in Actions tab
2. Ensure secrets are configured if using encrypted values

## Security Notes

- 🔒 Never commit actual passwords to git
- Use GitHub Secrets for sensitive data in CI/CD
- Review and comply with websites' terms of service when scraping

## License

MIT License

## Author

Created for Boeing recruitment monitoring