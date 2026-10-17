import smtplib, ssl, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to, subject, body_html):
    host = os.environ.get("SMTP_HOST", "")
    if not host:
        print(f"[email] SMTP not configured — skipping send to {to}")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = os.environ.get("SMTP_FROM", "noreply@localhost")
    msg["To"] = to
    msg.attach(MIMEText(body_html, "html"))
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, int(os.environ.get("SMTP_PORT", 465)), context=ctx) as s:
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        s.send_message(msg)

def send_verification(to, token):
    base = os.environ.get("BASE_URL", "http://localhost:8000")
    link = f"{base}/verify?token={token}"
    send_email(to, "Verify your account",
        f"<p>Click to verify:</p><p><a href='{link}'>{link}</a></p>")

def send_reset(to, token):
    base = os.environ.get("BASE_URL", "http://localhost:8000")
    link = f"{base}/reset?token={token}"
    send_email(to, "Password reset",
        f"<p>Reset your password:</p><p><a href='{link}'>{link}</a></p>")
