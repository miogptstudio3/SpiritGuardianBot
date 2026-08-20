import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}

# اولین ADMIN_IDS به صورت پیش‌فرض «سازنده» محسوب می‌شود.
# در نسخه‌های بعدی می‌توان مدیریت نقش‌ها را کاملاً از داخل پنل انجام داد.
ROLE_LEVELS = {
    "ویژه": 70,
    "مدیر": 60,
    "معاون مدیر": 50,
    "معاون ادمین": 40,
    "ادمین": 30,
    "معاون سازنده": 20,
    "سازنده": 10,
    "کاربر": 0,
}

ROLE_PERMISSIONS = {
    "ویژه": {"panel", "stats", "users", "broadcast", "give", "ban", "unban", "setrole", "addspirit", "maintenance"},
    "مدیر": {"panel", "stats", "users", "broadcast", "give", "ban", "unban", "setrole", "addspirit"},
    "معاون مدیر": {"panel", "stats", "users", "broadcast", "give", "ban", "unban", "addspirit"},
    "معاون ادمین": {"panel", "stats", "users", "give", "ban", "unban"},
    "ادمین": {"panel", "stats", "users", "give", "ban"},
    "معاون سازنده": {"panel", "stats", "users", "give"},
    "سازنده": {"panel", "stats", "users"},
    "کاربر": set(),
}

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN در فایل .env تنظیم نشده است.")
