import smtplib
from email.mime.text import MIMEText
from ._exceptions import ScraperError


def send_email(email_cfg: dict, subject: str, body: str):
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = email_cfg["sender"]
        msg["To"] = email_cfg["receiver"]

        with smtplib.SMTP(email_cfg["host"], email_cfg.get("port", 25)) as server:
            if email_cfg.get("tls"):
                server.starttls()
            if email_cfg.get("username"):
                server.login(email_cfg["username"], email_cfg["password"])
            server.send_message(msg)
    except Exception as exc:
        raise ScraperError(f"Email send failed: {exc}") from exc
