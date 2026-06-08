"""
邮件发送服务
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import load_email_config


def send_email(to_email: str, subject: str, body: str) -> bool:
    """发送邮件 — 用配置中的SMTP"""
    cfg = load_email_config()
    if not cfg["enabled"] or not cfg["sender"] or not cfg["password"]:
        print("[邮件提醒] 未配置SMTP，跳过发送")
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = cfg["sender"]
        msg["To"] = to_email or cfg.get("receiver", cfg["sender"])
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html", "utf-8"))

        with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"], timeout=10) as server:
            server.starttls()
            server.login(cfg["sender"], cfg["password"])
            server.sendmail(cfg["sender"], msg["To"], msg.as_string())
        print(f"[邮件提醒] 已发送到 {msg['To']}: {subject}")
        return True
    except Exception as e:
        print(f"[邮件提醒] 发送失败: {e}")
        return False
