# 👻 راهنمای محافظ ارواح (Spirit Guardian)

ربات بازی تلگرامی با موضوع ارواح، جن‌ها، مأموریت‌ها، فروشگاه، خانواده و Web App موبایل.

ساختار پروژه **تخت** است (بدون پوشه اضافی `webapp/`) تا بتوانید مستقیماً روی GitHub آپلود کنید و روی Render یا هر هاستی دیپلوی کنید.

## ساختار فایل‌ها

```
.
├── bot.py              # نقطه ورود ربات
├── web_app.py          # سرور Web App + API
├── database.py         # PostgreSQL + منطق دیتابیس
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

## اتصال به PostgreSQL

نسخه فعلی برای PostgreSQL آماده شده و دیگر از فایل SQLite استفاده نمی‌کند. کافی است متغیر `DATABASE_URL` را تنظیم کنید:

```env
DATABASE_URL=postgresql://USERNAME:PASSWORD@HOST:5432/DATABASE_NAME
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
ADMIN_IDS=123456789
```

با اولین اجرای ربات، جدول‌ها و داده‌های اولیه بازی به‌صورت خودکار ساخته می‌شوند. `schema_postgresql.sql` نیز برای ساخت دستی جدول‌ها در PostgreSQL قرار داده شده است.

نکته: اگر سرویس PostgreSQL شما یک URL با `postgres://` می‌دهد، برنامه آن را نیز قبول می‌کند.

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

این نسخه از **PostgreSQL** استفاده می‌کند. داده‌ها داخل سرویس PostgreSQL ذخیره می‌شوند و با ریستارت یا ریدیپلوی پاک نمی‌شوند.

روی **Render**:

1. یک **PostgreSQL** دیتابیس بسازید (یا از سرویس خارجی مثل Neon/Supabase استفاده کنید).
2. متغیر محیطی `DATABASE_URL` را با connection string پر کنید:
   ```
   DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME
   ```
3. نیازی به Persistent Disk برای فایل دیتابیس نیست (چون فایل SQLite دیگر استفاده نمی‌شود).

اگر سرویس PostgreSQL شما URL با `postgres://` بدهد، برنامه آن را هم قبول می‌کند.

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

## دیپلوی روی GitHub + Render (یک سرویس کافی است)

از نسخه ۲.۳ به بعد **ربات و وب‌اپ در یک پروسس** اجرا می‌شوند.

1. این پوشه را root ریپازیتوری GitHub بگذارید.
2. فقط **یک Web Service** روی Render بسازید:
   - **Start Command:** `python bot.py`
3. Environment Variables:
   - `BOT_TOKEN`
   - `ADMIN_IDS`
   - `DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME`
4. Persistent Disk با Mount Path: `/var/data`
5. بعد از Deploy، URL سرویس (مثلاً `https://xxx.onrender.com`) را در BotFather به‌عنوان **Menu Button / Web App** بگذارید.

نیازی به سرویس دوم برای وب‌اپ نیست.

## اتصال Web App به ربات

در BotFather یک Menu Button / Web App بسازید و URL سرویس وب را بدهید.

ورود فقط با `initData` معتبر تلگرام انجام می‌شود؛ کاربر نمی‌تواند با دستکاری `user_id` وارد حساب دیگری شود.

## نسخه

v2.5 — رفع باگ فروشگاه + دستورات بی‌پاسخ + فهرست دستورات:
- باگ فروشگاه: انرژی دیگر هنگام خرید اعمال نمی‌شود (فقط با استفاده از کوله‌پشتی) — جلوگیری از دوبرابر شدن انرژی
- یکسان‌سازی منطق خرید/مصرف بین ربات و Web App
- بهبود UI فروشگاه (نمایش اثر آیتم، برگشت صحیح به لیست، پیام خرید بهتر)
- پیاده‌سازی دستورات گمشده ادمین: /give /ban /unban /addspirit /addshop /broadcast
- اصلاح deny برای پشتیبانی همزمان از Message و CallbackQuery
- دستور /commands (و /help) با فهرست کامل همهٔ دستورات بازی و مدیریت

v2.4 — رفع باگ‌های PostgreSQL و سازگاری:
- حذف کد باقی‌مانده SQLite (makedirs روی مسیر URL که باعث ایجاد پوشهٔ نامعتبر می‌شد)
- بارگذاری صحیح `.env` در `web_app.py` و `database.py`
- CREATOR_ID داینامیک از `ADMIN_IDS` / متغیر محیطی (دیگر hardcode نیست)
- اصلاح adapter آیوسکیولایت (حذف بازنویسی خطرناک MIN/MAX که توابع aggregate را می‌شکست)
- به‌روزرسانی README برای حذف ارجاعات قدیمی به فایل SQLite و Persistent Disk
- بهبود پشتیبانی row_factory در لایهٔ سازگاری

v2.3 — رفع باگ‌های مهم:
- پایداری ربات (حلقهٔ تلاش مجدد + هندلر خطای سراسری + لاگ)
- بخش جن‌ها (برگشت صحیح encounter + مسیر دیتابیس یکسان + مبارزه دوباره)
- سیستم ارتقای سکه (تا +۵۰٪ پاداش)
- دکمه موجودی و منوی بهتر
- جن‌ها و داستان‌های بیشتر
