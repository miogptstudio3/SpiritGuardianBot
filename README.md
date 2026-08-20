# 👻 راهنمای محافظ ارواح (Spirit Guardian)

ربات بازی تلگرامی با موضوع ارواح، جن‌ها، مأموریت‌ها، فروشگاه، خانواده و Web App موبایل.

ساختار پروژه **تخت** است (بدون پوشه اضافی `webapp/`) تا بتوانید مستقیماً روی GitHub آپلود کنید و روی Render یا هر هاستی دیپلوی کنید.

## ساختار فایل‌ها

```
.
├── bot.py              # نقطه ورود ربات
├── web_app.py          # سرور Web App + API
├── database.py         # SQLite + منطق دیتابیس
├── admin.py            # پنل مدیریت و دستورات ادمین
├── game.py / start.py  # منطق بازی و منوها
├── config.py           # تنظیمات و اختیارات نقش‌ها
├── index.html          # رابط Web App
├── static/             # CSS و JS وب‌اپ
├── requirements.txt
├── requirements-web.txt
├── .env.example
└── .gitignore
```

## اجرای محلی ربات

1. Python 3.11+
2. `pip install -r requirements.txt`
3. `cp .env.example .env` و مقداردهی `BOT_TOKEN` و `ADMIN_IDS`
4. `python bot.py`

## اجرای Web App

```bash
pip install -r requirements-web.txt
python web_app.py
```

پورت پیش‌فرض از متغیر `PORT` خوانده می‌شود (مناسب Render).

## نگهداری دائمی داده‌ها (مهم)

SQLite به صورت پیش‌فرض در مسیر زیر ذخیره می‌شود:

- اگر پوشه `/var/data` وجود داشته باشد → `/var/data/spirits.db`
- در غیر این صورت → `spirits.db` در پوشه فعلی

روی **Render**:

1. به Web Service یک **Persistent Disk** وصل کنید.
2. Mount Path را بگذارید: `/var/data`
3. (اختیاری) Environment Variable:
   ```
   DB_PATH=/var/data/spirits.db
   ```

کد به صورت خودکار پوشه والد دیتابیس را می‌سازد. با این کار بعد از Redeploy یا Restart، پیشرفت بازیکنان پاک نمی‌شود.

**نکته:** فایل‌سیستم محلی Render بدون Persistent Disk موقتی است و با Deploy از بین می‌رود.

## اختیارات مدیریتی گسترش‌یافته

رتبه‌ها (از بالاترین):

| رتبه | سطح |
|------|-----|
| 💎 ویژه | 100 |
| 👑 مدیر | 80 |
| 🛡️ معاون مدیر | 60 |
| 🔰 معاون ادمین | 50 |
| ⚙️ ادمین | 40 |
| 🧩 معاون سازنده | 25 |
| 🔨 سازنده | 20 |
| 👤 کاربر | 0 |

هر رتبه فقط می‌تواند رتبه‌های **پایین‌تر** از خودش را مدیریت کند. حساب سازنده اصلی (`CREATOR_ID`) محافظت‌شده است.

دسترسی‌های جدید نسبت به نسخه قبل:

- دسترسی گسترده‌تر به `give` / `ban` / `tempban` / `warn` برای رتبه‌های میانی
- دسترسی به فروشگاه و لاگ برای معاون مدیر و بالاتر
- پشتیبانی از `setlevel`، `setgems`، `sethealth`، `deleteuser`، `reset`، `maintenance` در سطح ویژه/مدیر

دستورات کلیدی:

- `/panel` — پنل شیشه‌ای
- `/usersearch نام یا ID`
- `/setrole ID رتبه`
- `/give ID coins energy`
- `/setgems ID مقدار`
- `/sethealth ID مقدار`
- `/setlevel ID سطح`
- `/warn ID دلیل`
- `/tempban ID دقیقه دلیل`
- `/adminlogs`
- `/addspirit` و `/addshop`

اولین شناسه موجود در `ADMIN_IDS` به صورت پیش‌فرض سازنده شناخته می‌شود.

## دیپلوی روی GitHub + Render

1. این پوشه را مستقیماً به عنوان root یک ریپازیتوری GitHub بگذارید (بدون پوشه والد اضافی).
2. دو سرویس بسازید (یا یک سرویس برای ربات و یکی برای وب):
   - **Bot**: Start Command → `python bot.py`
   - **Web**: Start Command → `python web_app.py`
3. Environment Variables مشترک:
   - `BOT_TOKEN`
   - `ADMIN_IDS`
   - `DB_PATH=/var/data/spirits.db`
4. Persistent Disk روی `/var/data` برای هر دو سرویس (یا یک دیسک مشترک اگر ممکن بود).

## اتصال Web App به ربات

در BotFather یک Menu Button / Web App بسازید و URL سرویس وب را بدهید.

ورود فقط با `initData` معتبر تلگرام انجام می‌شود؛ کاربر نمی‌تواند با دستکاری `user_id` وارد حساب دیگری شود.

## نسخه

v2.2 — ساختار تخت برای GitHub، تضمین ماندگاری دیتابیس، اختیارات ادمین گسترش‌یافته.
