"""
Phase 4: Notification Agent

Sends an email alert (via Gmail SMTP) when any Critical-importance
articles are found — so you get notified on your phone immediately,
instead of waiting to check the poster in the evening.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, NOTIFY_TO_EMAIL

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465


def send_critical_alert(articles):
    """
    Filters for Critical-importance articles and emails a short alert
    listing them. Does nothing if there are no Critical articles, or
    if email credentials aren't configured.
    """
    critical_articles = [a for a in articles if a.get("importance") == "Critical"]

    if not critical_articles:
        print("[Notifier] No Critical articles — no alert sent.")
        return

    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("[Notifier] Skipped — GMAIL_ADDRESS/GMAIL_APP_PASSWORD not set.")
        return

    to_email = NOTIFY_TO_EMAIL or GMAIL_ADDRESS

    subject = f"🚨 {len(critical_articles)} Critical news update(s) today"

    body_lines = ["Today's CRITICAL current affairs news:\n"]
    for a in critical_articles:
        body_lines.append(f"• [{a.get('category', 'General')}] {a['title']}")
        summary = a.get("ai_summary", "")
        if summary:
            body_lines.append(f"  {summary}")
        body_lines.append(f"  Source: {a.get('source', '')}\n")

    body = "\n".join(body_lines)

    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        print(f"[Notifier] Alert email sent to {to_email}.")
    except smtplib.SMTPException as e:
        print(f"[Notifier] Failed to send email: {e}")
