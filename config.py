import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CREATOR_ID = 6227792513
ADMIN_IDS = {
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}

# سطح بالاتر = قدرت بیشتر. ویژه بالاترین رتبه است.
# اولین شناسه موجود در ADMIN_IDS به صورت پیش‌فرض «سازنده» شناخته می‌شود.
ROLE_LEVELS = {
    "ویژه": 100,
    "مدیر": 80,
    "معاون مدیر": 60,
    "معاون ادمین": 50,
    "ادمین": 40,
    "معاون سازنده": 25,
    "سازنده": 20,
    "کاربر": 0,
}

# اختیارات گسترش‌یافته — هر رتبه قدرت بیشتری نسبت به نسخه قبل دارد
ROLE_PERMISSIONS = {
    "ویژه": {
        "panel", "stats", "users", "broadcast", "give", "ban", "unban",
        "setrole", "addspirit", "maintenance", "deleteuser", "reset",
        "shop", "logs", "tempban", "warn", "setlevel", "setgems", "sethealth"
    },
    "مدیر": {
        "panel", "stats", "users", "broadcast", "give", "ban", "unban",
        "setrole", "addspirit", "shop", "logs", "tempban", "warn",
        "setlevel", "setgems", "sethealth"
    },
    "معاون مدیر": {
        "panel", "stats", "users", "broadcast", "give", "ban", "unban",
        "addspirit", "shop", "logs", "tempban", "warn", "setgems", "sethealth"
    },
    "معاون ادمین": {
        "panel", "stats", "users", "give", "ban", "unban",
        "logs", "tempban", "warn", "setgems", "sethealth"
    },
    "ادمین": {
        "panel", "stats", "users", "give", "ban", "unban",
        "tempban", "warn", "setgems"
    },
    "معاون سازنده": {
        "panel", "stats", "users", "give", "setgems"
    },
    "سازنده": {
        "panel", "stats", "users", "give"
    },
    "کاربر": set(),
}

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN در فایل .env تنظیم نشده است.")
