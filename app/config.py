"""
JobPilot 配置中心
"""
import json
import os
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 加载 .env 文件
_env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(_env_file):
    with open(_env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())
SECRET_KEY = os.getenv("SECRET_KEY", "jobpilot-dev-2026-keep-it-secret")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7
DB_URL = f"sqlite:///{os.path.join(BASE_DIR, 'jobpilot.db')}"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"

EMAIL_CONFIG_FILE = Path(BASE_DIR) / "email_config.json"
NOTIFIED_FILE = Path(BASE_DIR) / "notified_interviews.json"
INVITE_CONFIG_FILE = Path(BASE_DIR) / "invite_config.json"


def load_invite_config():
    if INVITE_CONFIG_FILE.exists():
        return json.loads(INVITE_CONFIG_FILE.read_text(encoding="utf-8"))
    return {"enabled": False, "code": "jobpilot2026"}


def save_invite_config(cfg):
    INVITE_CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def load_email_config():
    if EMAIL_CONFIG_FILE.exists():
        return json.loads(EMAIL_CONFIG_FILE.read_text(encoding="utf-8"))
    return {"enabled": False, "smtp_host": "smtp.qq.com", "smtp_port": 587,
            "sender": "", "password": "", "receiver": ""}


def save_email_config(cfg):
    EMAIL_CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def load_notified():
    if NOTIFIED_FILE.exists():
        return set(json.loads(NOTIFIED_FILE.read_text()))
    return set()


def save_notified(s):
    NOTIFIED_FILE.write_text(json.dumps(list(s)), encoding="utf-8")


# 邀请码库（管理员生成的邮箱专属邀请码）
INVITES_FILE = Path(BASE_DIR) / "invites.json"


def load_invites() -> list[dict]:
    """返回 [{code, email, used, created_at}, ...]"""
    if INVITES_FILE.exists():
        return json.loads(INVITES_FILE.read_text(encoding="utf-8"))
    return []


def save_invites(invites: list[dict]):
    INVITES_FILE.write_text(json.dumps(invites, ensure_ascii=False, indent=2), encoding="utf-8")


def find_valid_invite(code: str) -> dict | None:
    """查找有效的邀请码（未使用），兼容旧版通用邀请码"""
    # 先检查通用邀请码
    invite_cfg = load_invite_config()
    if invite_cfg["enabled"] and code == invite_cfg["code"]:
        return {"code": code, "email": "通用邀请码", "used": False, "type": "global"}
    # 再检查邮箱专属邀请码
    invites = load_invites()
    for inv in invites:
        if inv["code"] == code and not inv.get("used", False):
            return inv
    return None


def mark_invite_used(code: str):
    """标记邀请码已使用"""
    invites = load_invites()
    for inv in invites:
        if inv["code"] == code:
            inv["used"] = True
            inv["used_at"] = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")
    save_invites(invites)


# — 密码重置 —
RESETS_FILE = Path(BASE_DIR) / "password_resets.json"


def load_resets() -> list[dict]:
    if RESETS_FILE.exists():
        return json.loads(RESETS_FILE.read_text(encoding="utf-8"))
    return []


def save_resets(resets: list[dict]):
    RESETS_FILE.write_text(json.dumps(resets, ensure_ascii=False, indent=2), encoding="utf-8")


def find_reset(email: str, code: str) -> dict | None:
    from datetime import datetime, timezone
    resets = load_resets()
    now = datetime.now(timezone.utc)
    for r in resets:
        if r["email"] == email and r["code"] == code and not r.get("used"):
            expires = datetime.fromisoformat(r["expires_at"])
            if now < expires.replace(tzinfo=timezone.utc):
                return r
    return None


def mark_reset_used(email: str, code: str):
    resets = load_resets()
    for r in resets:
        if r["email"] == email and r["code"] == code:
            r["used"] = True
    save_resets(resets)
