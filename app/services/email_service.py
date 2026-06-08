"""
邮件发送服务
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import load_email_config


def send_email(to_email: str, subject: str, body: str) -> bool:
    """发送邮件 — 优先 SSL 465，回退 STARTTLS 587"""
    cfg = load_email_config()
    if not cfg["enabled"] or not cfg["sender"] or not cfg["password"]:
        print("[邮件提醒] 未配置SMTP，跳过发送")
        return False

    msg = MIMEMultipart()
    msg["From"] = cfg["sender"]
    msg["To"] = to_email or cfg.get("receiver", cfg["sender"])
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html", "utf-8"))

    host = cfg["smtp_host"]
    password = cfg["password"]

    # 方法1: SMTP_SSL 端口 465（Renderer 友好）
    try:
        with smtplib.SMTP_SSL(host, 465, timeout=10) as server:
            server.login(cfg["sender"], password)
            server.sendmail(cfg["sender"], msg["To"], msg.as_string())
        print(f"[邮件提醒] SSL:465 已发送到 {msg['To']}: {subject}")
        return True
    except Exception as e:
        print(f"[邮件提醒] SSL:465 失败: {e}")

    # 方法2: STARTTLS 端口 587
    try:
        with smtplib.SMTP(host, 587, timeout=10) as server:
            server.starttls()
            server.login(cfg["sender"], password)
            server.sendmail(cfg["sender"], msg["To"], msg.as_string())
        print(f"[邮件提醒] STARTTLS:587 已发送到 {msg['To']}: {subject}")
        return True
    except Exception as e:
        print(f"[邮件提醒] STARTTLS:587 失败: {e}")

    return False
