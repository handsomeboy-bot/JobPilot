"""
后台面试提醒线程
"""
import threading
import time
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models.interview import Interview
from app.models.application import Application
from app.config import load_email_config, load_notified, save_notified
from app.services.email_service import send_email


def check_and_notify():
    """后台线程 — 每5分钟检查即将到来的面试，发邮件提醒"""
    while True:
        try:
            db = SessionLocal()
            cfg = load_email_config()
            if cfg["enabled"]:
                now = datetime.now(timezone.utc)
                soon = now + timedelta(hours=1)
                interviews = db.query(Interview).join(Application).filter(
                    Interview.scheduled_time >= now,
                    Interview.scheduled_time <= soon,
                    Interview.interview_status == "scheduled",
                ).all()

                notified = load_notified()
                for iv in interviews:
                    key = f"{iv.id}_{iv.scheduled_time.strftime('%Y%m%d%H%M')}"
                    if key not in notified:
                        body = f"""
                        <h2>⏰ 面试提醒 — {iv.application.company}</h2>
                        <p><b>岗位：</b>{iv.application.position}</p>
                        <p><b>轮次：</b>{iv.round} · {iv.interview_type}</p>
                        <p><b>时间：</b>{iv.scheduled_time.strftime('%Y-%m-%d %H:%M')}</p>
                        <p><b>面试官：</b>{iv.interviewer or '待定'}</p>
                        <p><b>备注：</b>{iv.notes or '无'}</p>
                        <hr>
                        <p style='color:#666;'>此邮件由 JobPilot 自动发送 — 祝你面试顺利！🚀</p>
                        """
                        send_email(cfg.get("receiver", cfg["sender"]),
                                   f"面试提醒 — {iv.application.company} {iv.application.position}",
                                   body)
                        notified.add(key)
                save_notified(notified)
            db.close()
        except Exception as e:
            print(f"[邮件提醒] 检查出错: {e}")
        time.sleep(300)


def start_reminder_thread():
    t = threading.Thread(target=check_and_notify, daemon=True)
    t.start()
