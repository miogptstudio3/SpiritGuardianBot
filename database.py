import aiosqlite
import os
from datetime import datetime, timezone

# Render's local filesystem is ephemeral. If a persistent disk is mounted at
# /var/data, keep the SQLite database there so player progress survives deploys.
# You can override this with DB_PATH in Render Environment Variables.
DEFAULT_DB_PATH = "/var/data/spirits.db" if os.path.isdir("/var/data") else "spirits.db"
DB_PATH = os.getenv("DB_PATH", DEFAULT_DB_PATH)
# Always ensure the directory exists so SQLite can create the file (persistent disk or local)
_db_parent = os.path.dirname(DB_PATH)
if _db_parent:
    os.makedirs(_db_parent, exist_ok=True)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            coins INTEGER NOT NULL DEFAULT 100,
            energy INTEGER NOT NULL DEFAULT 10,
            max_health INTEGER NOT NULL DEFAULT 100,
            health INTEGER NOT NULL DEFAULT 100,
            soul_gems INTEGER NOT NULL DEFAULT 0,
            xp INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 1,
            spirits_sent INTEGER NOT NULL DEFAULT 0,
            cleanses INTEGER NOT NULL DEFAULT 0,
            last_daily TEXT,
            gender TEXT,
            mind_power INTEGER NOT NULL DEFAULT 1,
            body_power INTEGER NOT NULL DEFAULT 1,
            spirit_power INTEGER NOT NULL DEFAULT 1,
            training_points INTEGER NOT NULL DEFAULT 0,
            last_training TEXT
        );

        CREATE TABLE IF NOT EXISTS spirits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            request TEXT NOT NULL,
            difficulty INTEGER NOT NULL DEFAULT 1,
            reward_coins INTEGER NOT NULL DEFAULT 50,
            reward_xp INTEGER NOT NULL DEFAULT 30,
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS user_spirits (
            user_id INTEGER NOT NULL,
            spirit_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            PRIMARY KEY(user_id, spirit_id)
        );

        CREATE TABLE IF NOT EXISTS staff (
            user_id INTEGER PRIMARY KEY,
            role TEXT NOT NULL DEFAULT 'ادمین',
            added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS moderation (
            user_id INTEGER PRIMARY KEY,
            banned INTEGER NOT NULL DEFAULT 0,
            ban_until TEXT,
            reason TEXT
        );

        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            admin_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            target_id INTEGER,
            details TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS shop_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            price_coins INTEGER NOT NULL DEFAULT 0,
            price_gems INTEGER NOT NULL DEFAULT 0,
            energy_gain INTEGER NOT NULL DEFAULT 0,
            mission_bonus INTEGER NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 1,
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS inventory (
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(user_id, item_id)
        );

        CREATE TABLE IF NOT EXISTS regions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, description TEXT NOT NULL, unlock_level INTEGER NOT NULL DEFAULT 1, active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS spirits_story (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, age INTEGER, type TEXT NOT NULL, region_id INTEGER NOT NULL,
            difficulty INTEGER NOT NULL DEFAULT 1, status TEXT NOT NULL DEFAULT 'سرگردان', request TEXT NOT NULL, story TEXT NOT NULL,
            reward_coins INTEGER NOT NULL DEFAULT 50, reward_xp INTEGER NOT NULL DEFAULT 30, active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS spirit_clues (
            id INTEGER PRIMARY KEY AUTOINCREMENT, spirit_id INTEGER NOT NULL, clue_order INTEGER NOT NULL, text TEXT NOT NULL, correct_option TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS spirit_progress (
            user_id INTEGER NOT NULL, spirit_id INTEGER NOT NULL, clue_index INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'active',
            PRIMARY KEY(user_id, spirit_id)
        );

        CREATE TABLE IF NOT EXISTS demons (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, type TEXT NOT NULL, rank INTEGER NOT NULL DEFAULT 1,
            power INTEGER NOT NULL DEFAULT 50, defense INTEGER NOT NULL DEFAULT 20, health INTEGER NOT NULL DEFAULT 100, corruption INTEGER NOT NULL DEFAULT 100,
            temperament TEXT NOT NULL, ability TEXT NOT NULL, story TEXT NOT NULL, region_id INTEGER NOT NULL, reward_coins INTEGER NOT NULL DEFAULT 80, reward_xp INTEGER NOT NULL DEFAULT 50, active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS demon_encounters (
            user_id INTEGER NOT NULL, demon_id INTEGER NOT NULL, health INTEGER NOT NULL, corruption INTEGER NOT NULL, stage INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'active', PRIMARY KEY(user_id, demon_id)
        );

        CREATE TABLE IF NOT EXISTS currencies (
            key TEXT PRIMARY KEY, value INTEGER NOT NULL, description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS marriages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user1_id, user2_id)
        );

        CREATE TABLE IF NOT EXISTS children (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent1_id INTEGER NOT NULL,
            parent2_id INTEGER,
            name TEXT NOT NULL,
            age INTEGER NOT NULL DEFAULT 0,
            happiness INTEGER NOT NULL DEFAULT 80,
            health INTEGER NOT NULL DEFAULT 100,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cur = await db.execute("SELECT COUNT(*) FROM spirits")
        count = (await cur.fetchone())[0]
        if count == 0:
            await db.executemany(
                """INSERT INTO spirits
                (name, description, request, difficulty, reward_coins, reward_xp)
                VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    ("پیرمرد فانوس‌دار",
                     "روح پیرمردی که هر شب کنار یک جاده قدیمی ظاهر می‌شود.",
                     "فانوس گمشده‌اش را پیدا کن.",
                     1, 60, 35),
                    ("دختر عمارت خاموش",
                     "روحی که در یک عمارت متروکه گرفتار خاطرات گذشته است.",
                     "راز اتاق بسته را کشف کن.",
                     2, 110, 70),
                    ("نگهبان چاه",
                     "روح نگهبانی که هنوز از چاهی قدیمی محافظت می‌کند.",
                     "دلیل ماندنش را پیدا کن.",
                     3, 180, 110),
                ]
            )
        # فروشگاه اولیه
        cur = await db.execute("SELECT COUNT(*) FROM shop_items")
        shop_count = (await cur.fetchone())[0]
        if shop_count == 0:
            await db.executemany(
                """INSERT INTO shop_items
                (name, description, category, price_coins, price_gems, energy_gain, mission_bonus, quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    ("🍵 چای روحانی", "یک استکان چای برای بازیابی انرژی.", "🍵 خوراکی", 35, 0, 3, 0, 1),
                    ("🫖 چای مخصوص نگهبان", "چای ویژه برای محافظان خسته.", "🍵 خوراکی", 90, 0, 8, 0, 1),
                    ("🍖 کباب روحانی", "کباب داغ و خوش‌طعم برای محافظ.", "🍵 خوراکی", 80, 0, 2, 5, 1),
                    ("🍢 کباب ویژه محافظ", "کباب مخصوص بعد از مأموریت‌های سخت.", "🍵 خوراکی", 180, 1, 5, 12, 1),
                    ("🍵🍖 چای و کباب مخصوص", "بسته کامل استراحت محافظ.", "🍵 خوراکی", 250, 2, 10, 15, 1),
                    ("🕯️ فانوس روح", "افزایش شانس موفقیت مأموریت.", "🧿 ابزار محافظ", 150, 0, 0, 8, 1),
                    ("🔮 مهر محافظ", "محافظی جادویی که به مأموریت بعدی کمک می‌کند.", "🧿 ابزار محافظ", 250, 1, 0, 15, 1),
                    ("⚡ انرژی روحی", "بسته انرژی برای محافظ.", "⚡ انرژی", 60, 0, 10, 0, 1),
                    ("📜 طومار احضار", "یک مأموریت ویژه به دفتر ارواح اضافه می‌کند.", "📜 مأموریتی", 400, 3, 0, 20, 1),
                    ("🎁 جعبه اسرار", "یک آیتم تصادفی از فروشگاه.", "💎 ویژه", 500, 5, 0, 10, 1),
                ]
            )

        # Migration for existing databases.
        for statement in [
            "ALTER TABLE users ADD COLUMN max_health INTEGER NOT NULL DEFAULT 100",
            "ALTER TABLE users ADD COLUMN health INTEGER NOT NULL DEFAULT 100",
            "ALTER TABLE users ADD COLUMN light INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN gender TEXT",
            "ALTER TABLE moderation ADD COLUMN ban_until TEXT",
            "ALTER TABLE moderation ADD COLUMN reason TEXT",
            "ALTER TABLE users ADD COLUMN mind_power INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE users ADD COLUMN body_power INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE users ADD COLUMN spirit_power INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE users ADD COLUMN training_points INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN last_training TEXT",
        ]:
            try:
                await db.execute(statement)
            except Exception:
                pass


        # Story RPG seed data
        cur = await db.execute("SELECT COUNT(*) FROM regions")
        if (await cur.fetchone())[0] == 0:
            await db.executemany("INSERT INTO regions(name,description,unlock_level) VALUES (?,?,?)", [
                ("🏚️ روستای متروکه","خانه‌های خاموش و نخستین پرونده‌های ارواح.",1),
                ("🌲 جنگل مه‌آلود","جنگلی که صداهای ناشناخته در مه آن می‌پیچد.",5),
                ("🏙️ شهر خاموش","شهری که مردمش رازهای زیادی را پنهان کرده‌اند.",8),
                ("🪦 گورستان قدیمی","محل تجمع روح‌های خشمگین و پرونده‌های دشوار.",12),
                ("🏰 عمارت فراموش‌شده","عمارت متروکه با یک راز قدیمی.",16),
                ("🌊 دهکده غرق‌شده","بخشی از روستا زیر آب مانده و داستانش تمام نشده است.",20),
                ("🌑 سرزمین سایه‌ها","مرزی میان جهان انسان‌ها و موجودات سایه‌ای.",25),
                ("🚪 دروازه دنیای پسین","آخرین مرز راهنمایان ارواح.",30),
            ])
        cur=await db.execute("SELECT COUNT(*) FROM spirits_story")
        if (await cur.fetchone())[0] == 0:
            await db.executemany("INSERT INTO spirits_story(name,age,type,region_id,difficulty,status,request,story,reward_coins,reward_xp) VALUES (?,?,?,?,?,?,?,?,?,?)", [
                ("پیرمرد نامه‌به‌دست",72,"روح سرگردان",1,1,"سرگردان","پیدا کردن سرنوشت نامه‌ای که برای دخترش نوشته بود","پیرمرد هر شب کنار خانه قدیمی منتظر خبری است که هیچ‌وقت به او نرسیده.",90,60),
                ("آریا",19,"روح خشمگین",1,2,"سرگردان","کشف حقیقت یک اتفاق قدیمی","آریا باور دارد سه نفر درباره ناپدیدشدنش دروغ گفته‌اند.",160,110),
                ("دختر عمارت",24,"روح سرگردان",5,3,"سرگردان","باز کردن اتاق مهرشده","او خاطره آخرین شب زندگی‌اش را به یاد نمی‌آورد و کلید اتاق گم شده است.",260,180),
            ])
        cur=await db.execute("SELECT COUNT(*) FROM spirit_clues")
        if (await cur.fetchone())[0] == 0:
            await db.executemany("INSERT INTO spirit_clues(spirit_id,clue_order,text,correct_option) VALUES (?,?,?,?)", [
                (1,1,"روی میز خانه، نامه‌ای پاره شده پیدا می‌کنی. کجا را بررسی می‌کنی؟","🔎 نامه"),
                (1,2,"نام گیرنده روی پاکت پاک شده. سرنخ بعدی کجاست؟","🏚️ خانه"),
                (1,3,"همسایه پیر چیزی درباره نامه می‌داند.","🗣️ شاهد"),
                (2,1,"سه شاهد سه روایت متفاوت دارند.","🗣️ صحبت با شاهد"),
                (2,2,"یکی از روایت‌ها با یک ساعت قدیمی تناقض دارد.","🔎 بررسی ساعت"),
                (2,3,"حقیقت در زیرزمین خانه پنهان شده.","🏚️ بررسی زیرزمین"),
                (3,1,"روی در اتاق مهرشده نمادی قدیمی دیده می‌شود.","🔮 بررسی مهر"),
                (3,2,"کلید در کتابخانه پنهان شده است.","📚 جستجوی کتابخانه"),
                (3,3,"آخرین خاطره دختر در دفتر خاطرات ثبت شده.","📖 خواندن دفتر"),
            ])
        cur=await db.execute("SELECT COUNT(*) FROM demons")
        if (await cur.fetchone())[0] == 0:
            await db.executemany("INSERT INTO demons(name,type,rank,power,defense,health,corruption,temperament,ability,story,region_id,reward_coins,reward_xp) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", [
                ("جن سرکش","جن سرکش",2,90,35,220,70,"خصمانه","موج سایه","موجودی که به یک مکان متروکه وابسته شده است.",1,140,90),
                ("سایه‌خوار","سایه آلوده",3,140,55,420,84,"خنثی","بلعیدن انرژی","موجودی که از ترس بازدیدکنندگان نیرو می‌گیرد.",2,240,160),
                ("نگهبان سیاه","موجود نفرین‌شده",5,260,100,850,96,"نگهبان","مهر تاریکی","نگهبانی که زیر یک نفرین قدیمی گرفتار شده است.",5,600,420),
            ])
        cur=await db.execute("SELECT COUNT(*) FROM currencies")
        if (await cur.fetchone())[0] == 0:
            await db.executemany("INSERT INTO currencies(key,value,description) VALUES (?,?,?)", [
                ("starting_coins",100,"سکه شروع"),("starting_energy",10,"انرژی شروع"),("starting_gems",0,"کریستال شروع"),("starting_light",0,"نور پسین"),
                ("daily_coins",100,"پاداش روزانه سکه"),("daily_energy",5,"پاداش روزانه انرژی")
            ])

        # داستان‌های جدید و سخت‌تر — INSERT شرطی تا با دیتابیس قدیمی هم اضافه شوند.
        extra_stories = [
            # name, age, type, region_id, difficulty, status, request, story, reward_coins, reward_xp
            ("راز ناقوس نیمه‌شب", 31, "روح نگهبان", 2, 4, "سرگردان",
             "شناسایی صدای ناقوسی که هر شب پیش از ناپدیدشدن یک نفر شنیده می‌شود.",
             "در جنگل مه‌آلود، ناقوسی بدون برج هر نیمه‌شب به صدا درمی‌آید. هرکس دنبال صدا برود، یک خاطره مهم را از دست می‌دهد.", 420, 300),
            ("پرونده ساعت سیزدهم", 46, "روح زمان‌گمشده", 3, 5, "سرگردان",
             "پیدا کردن ساعتی که سیزدهمین ضربه را ثبت می‌کند.",
             "در شهر خاموش، همه ساعت‌ها روی یک زمان متوقف شده‌اند؛ جز ساعتی که گفته می‌شود می‌تواند یک تصمیم گذشته را آشکار کند.", 650, 500),
            ("مهمان اتاق صفر", 27, "روح ناشناس", 4, 5, "سرگردان",
             "کشف اینکه چه کسی هر شب وارد اتاق صفر می‌شود.",
             "در گورستان قدیمی، نگهبان از اتاقی حرف می‌زند که در نقشه وجود ندارد. هر سرنخ، سرنخ قبلی را زیر سؤال می‌برد.", 720, 560),
            ("نامه‌ای از زیر آب", 63, "روح غرق‌شده", 6, 6, "سرگردان",
             "خواندن نامه‌ای که پس از سال‌ها از دهکده غرق‌شده بازگشته است.",
             "نامه‌ای خشک و سالم از خانه‌ای بیرون می‌آید که دهه‌ها زیر آب بوده. نویسنده آن را با تاریخ فردا امضا کرده است.", 900, 720),
            ("دادگاه سایه‌ها", 88, "روح داور", 7, 7, "سرگردان",
             "تشخیص حقیقت میان سه خاطره متناقض.",
             "در سرزمین سایه‌ها، سه روح ادعا می‌کنند صاحب یک خاطره واحد هستند. فقط یکی از روایت‌ها می‌تواند با شواهد سازگار باشد.", 1200, 950),
        ]
        for st in extra_stories:
            cur = await db.execute("SELECT id FROM spirits_story WHERE name=?", (st[0],))
            if not await cur.fetchone():
                await db.execute(
                    """INSERT INTO spirits_story
                    (name,age,type,region_id,difficulty,status,request,story,reward_coins,reward_xp)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""", st)

        extra_clues = {
            "راز ناقوس نیمه‌شب": [
                ("صدای ناقوس فقط وقتی شنیده می‌شود که مه از سمت شمال حرکت کند. چه چیزی را بررسی می‌کنی؟","🧭 جهت مه"),
                ("روی تنه درختی علامتی دیده می‌شود که با زمان صدا همخوانی دارد.","🔎 علامت درخت"),
                ("سه شاهد زمان متفاوتی گفته‌اند؛ کدام شاهد مسیر ناقوس را واقعاً دیده؟","🗣️ مقایسه شاهدها"),
                ("ردپاها به جایی می‌رسند که هیچ ناقوسی در آن نیست.","🌫️ بررسی نقطه بی‌ناقوس"),
            ],
            "پرونده ساعت سیزدهم": [
                ("ساعت فقط یک بار در شب سیزدهمین ضربه را می‌زند. چه چیزی با آن تغییر می‌کند؟","🕰️ بررسی عقربه‌ها"),
                ("در دفتر شهر، همان روز یک نفر دو بار ثبت شده است.","📖 مقایسه دفتر"),
                ("یکی از شاهدها زمان را عمداً یک ساعت عقب گفته است.","🗣️ بازجویی دقیق"),
                ("عدد سیزده روی دیوار با نام یک ساختمان پاک‌شده همراه است.","🏙️ پیدا کردن ساختمان"),
            ],
            "مهمان اتاق صفر": [
                ("در نقشه عمارت، بین اتاق ۱ و ۲ فاصله‌ای غیرعادی وجود دارد.","🗺️ بررسی نقشه"),
                ("کلید اتاق صفر هیچ دندانه‌ای ندارد اما قفل را باز می‌کند.","🔑 بررسی کلید"),
                ("مهمان هر بار پیش از ورود، نام یکی از نگهبانان را می‌گوید.","🗣️ مقایسه نام‌ها"),
                ("دفتر نگهبان نشان می‌دهد یک نفر هیچ‌وقت در شیفت ثبت نشده است.","📚 بررسی دفتر نگهبان"),
            ],
            "نامه‌ای از زیر آب": [
                ("کاغذ خشک است اما نمک آب در لبه آن باقی مانده.","🧂 بررسی نمک"),
                ("تاریخ نامه یک روز جلوتر از تاریخ فعلی است.","📅 بررسی تاریخ"),
                ("نام گیرنده با نامی روی زنگ خانه غرق‌شده یکسان است.","🔔 مقایسه نام"),
                ("آخرین جمله نامه به چیزی اشاره می‌کند که هنوز ساخته نشده.","🏗️ بررسی نشانی"),
            ],
            "دادگاه سایه‌ها": [
                ("هر سه روح یک خاطره را با جزئیات متفاوت تعریف می‌کنند.","⚖️ مقایسه روایت‌ها"),
                ("فقط یکی از سه روایت با زمان طلوع ماه سازگار است.","🌙 بررسی زمان"),
                ("یک شاهد در هر سه روایت حضور دارد، اما جای او متفاوت است.","🗣️ تطبیق شاهد"),
                ("سند قدیمی یک نام را حذف کرده و نام دیگری را جایگزین کرده است.","📜 بررسی سند"),
                ("حقیقت نه در قدیمی‌ترین روایت، بلکه در تنها شاهد بی‌طرف پنهان است.","🔍 یافتن شاهد بی‌طرف"),
            ],
        }
        for story_name, clues in extra_clues.items():
            cur = await db.execute("SELECT id FROM spirits_story WHERE name=?", (story_name,))
            row = await cur.fetchone()
            if row:
                sid = row[0]
                for order, (text, correct) in enumerate(clues, 1):
                    cur = await db.execute(
                        "SELECT id FROM spirit_clues WHERE spirit_id=? AND clue_order=?",
                        (sid, order))
                    if not await cur.fetchone():
                        await db.execute(
                            "INSERT INTO spirit_clues(spirit_id,clue_order,text,correct_option) VALUES (?,?,?,?)",
                            (sid, order, text, correct))

        await db.commit()

async def ensure_user(user_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(user_id, name, coins, energy, soul_gems) VALUES (?, ?, COALESCE((SELECT value FROM currencies WHERE key='starting_coins'),100), COALESCE((SELECT value FROM currencies WHERE key='starting_energy'),10), COALESCE((SELECT value FROM currencies WHERE key='starting_gems'),0))",
            (user_id, name[:80])
        )
        await db.execute("UPDATE users SET name=? WHERE user_id=?", (name[:80], user_id))
        await db.commit()

async def set_gender(user_id: int, gender: str):
    if gender not in ("male", "female"):
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET gender=? WHERE user_id=?", (gender, user_id))
        await db.commit()
    return True

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return await cur.fetchone()

async def add_progress(user_id: int, coins: int, xp: int, spirit: bool=False, cleanse: bool=False):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE users SET coins=coins+?, xp=xp+?,
               spirits_sent=spirits_sent+?, cleanses=cleanses+?
               WHERE user_id=?""",
            (coins, xp, int(spirit), int(cleanse), user_id)
        )
        await db.execute(
            """UPDATE users SET level = 1 + CAST(xp / 250 AS INTEGER)
               WHERE user_id=?""", (user_id,)
        )
        await db.commit()

async def list_spirits():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM spirits WHERE active=1 ORDER BY difficulty, id")
        return await cur.fetchall()

async def get_spirit(spirit_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM spirits WHERE id=? AND active=1", (spirit_id,))
        return await cur.fetchone()

async def mark_spirit(user_id: int, spirit_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT status FROM user_spirits WHERE user_id=? AND spirit_id=?",
            (user_id, spirit_id)
        )
        row = await cur.fetchone()
        if row and row[0] == "sent":
            return False
        await db.execute(
            """INSERT INTO user_spirits(user_id, spirit_id, status)
               VALUES (?, ?, 'sent')
               ON CONFLICT(user_id, spirit_id) DO UPDATE SET status='sent'""",
            (user_id, spirit_id)
        )
        await db.commit()
        return True

async def daily_claim(user_id: int):
    today = datetime.now(timezone.utc).date().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT last_daily FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if row and row[0] == today:
            return False
        await db.execute(
            "UPDATE users SET coins=coins+100, energy=energy+5, last_daily=? WHERE user_id=?",
            (today, user_id)
        )
        await db.commit()
        return True

async def top_users(limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT name, level, spirits_sent, cleanses FROM users "
            "ORDER BY spirits_sent + cleanses DESC, xp DESC LIMIT ?",
            (limit,)
        )
        return await cur.fetchall()


async def get_role(user_id: int):
    from config import ROLE_LEVELS
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT role FROM staff WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if row:
            return row[0]
    from config import CREATOR_ID, ADMIN_IDS
    if user_id == CREATOR_ID:
        return "ویژه"
    return "سازنده" if user_id in ADMIN_IDS else "کاربر"

async def set_role(user_id: int, role: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO staff(user_id, role) VALUES (?, ?)
               ON CONFLICT(user_id) DO UPDATE SET role=excluded.role""",
            (user_id, role)
        )
        await db.commit()

async def remove_staff(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM staff WHERE user_id=?", (user_id,))
        await db.commit()

async def is_banned(user_id: int):
    from datetime import datetime, timezone
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT banned, ban_until FROM moderation WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if not row or not row[0]:
            return False
        if row[1]:
            try:
                if datetime.fromisoformat(row[1]) <= datetime.now(timezone.utc):
                    await db.execute("UPDATE moderation SET banned=0, ban_until=NULL WHERE user_id=?", (user_id,))
                    await db.commit()
                    return False
            except ValueError:
                pass
        return True

async def set_ban(user_id: int, banned: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO moderation(user_id, banned) VALUES (?, ?)
               ON CONFLICT(user_id) DO UPDATE SET banned=excluded.banned""",
            (user_id, int(banned))
        )
        await db.commit()

async def get_user_count():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        return (await cur.fetchone())[0]

async def get_spirit_count():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM spirits WHERE active=1")
        return (await cur.fetchone())[0]

async def get_staff_list():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT user_id, role, added_at FROM staff ORDER BY role, user_id")
        return await cur.fetchall()

async def admin_give(user_id: int, coins: int = 0, energy: int = 0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET coins=coins+?, energy=energy+? WHERE user_id=?",
            (coins, energy, user_id)
        )
        await db.commit()

async def add_spirit(name, description, request, difficulty, coins, xp):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO spirits(name, description, request, difficulty, reward_coins, reward_xp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, description, request, difficulty, coins, xp)
        )
        await db.commit()
        return cur.lastrowid


async def list_shop_items(category=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if category:
            cur = await db.execute(
                "SELECT * FROM shop_items WHERE active=1 AND category=? ORDER BY id",
                (category,)
            )
        else:
            cur = await db.execute(
                "SELECT * FROM shop_items WHERE active=1 ORDER BY id"
            )
        return await cur.fetchall()

async def get_shop_item(item_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM shop_items WHERE id=? AND active=1", (item_id,)
        )
        return await cur.fetchone()

async def buy_shop_item(user_id: int, item_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM shop_items WHERE id=? AND active=1", (item_id,)
        )
        item = await cur.fetchone()
        if not item:
            return False, "item_not_found"

        cur = await db.execute(
            "SELECT coins, soul_gems, energy FROM users WHERE user_id=?", (user_id,)
        )
        user = await cur.fetchone()
        if not user:
            return False, "user_not_found"

        if user["coins"] < item["price_coins"] or user["soul_gems"] < item["price_gems"]:
            return False, "not_enough"

        await db.execute(
            "UPDATE users SET coins=coins-?, soul_gems=soul_gems-?, energy=energy+? WHERE user_id=?",
            (item["price_coins"], item["price_gems"], item["energy_gain"], user_id)
        )
        await db.execute(
            """INSERT INTO inventory(user_id, item_id, quantity)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id, item_id)
               DO UPDATE SET quantity=quantity+excluded.quantity""",
            (user_id, item_id, item["quantity"])
        )
        await db.commit()
        return True, item

async def use_inventory_item(user_id: int, item_id: int):
    """مصرف واقعی یک آیتم از کیف و اعمال اثر آن به صورت اتمیک."""
    import random
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT i.quantity, s.* FROM inventory i
               JOIN shop_items s ON s.id=i.item_id
               WHERE i.user_id=? AND i.item_id=? AND i.quantity>0 AND s.active=1""",
            (user_id, item_id)
        )
        item = await cur.fetchone()
        if not item:
            return False, "این آیتم در کیف تو وجود ندارد."

        cur = await db.execute("SELECT energy, health, max_health FROM users WHERE user_id=?", (user_id,))
        user = await cur.fetchone()
        if not user:
            return False, "کاربر پیدا نشد."

        # جعبه اسرار: با مصرف آن یک آیتم تصادفی دیگر می‌گیری.
        if "جعبه اسرار" in item["name"]:
            cur = await db.execute("SELECT * FROM shop_items WHERE active=1 AND id<>? ORDER BY RANDOM() LIMIT 1", (item_id,))
            reward = await cur.fetchone()
            if not reward:
                return False, "فعلاً آیتم جایزه‌ای وجود ندارد."
            await db.execute(
                """INSERT INTO inventory(user_id,item_id,quantity) VALUES (?,?,?)
                   ON CONFLICT(user_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity""",
                (user_id, reward["id"], reward["quantity"])
            )
            effect_text = f"🎁 جایزه تصادفی: {reward['name']} × {reward['quantity']}"
        else:
            changes = []
            if item["energy_gain"]:
                await db.execute("UPDATE users SET energy=energy+? WHERE user_id=?", (item["energy_gain"], user_id))
                changes.append(f"💠 +{item['energy_gain']} انرژی")
            if item["mission_bonus"]:
                await db.execute("UPDATE users SET spirit_power=spirit_power+? WHERE user_id=?", (item["mission_bonus"], user_id))
                changes.append(f"🔮 +{item['mission_bonus']} قدرت روح")
            # اگر آیتم هیچ اثر عددی نداشت، حداقل XP کمی برای استفاده بده.
            if not changes:
                await db.execute("UPDATE users SET xp=xp+5 WHERE user_id=?", (user_id,))
                changes.append("✨ +5 XP")
            effect_text = " | ".join(changes)

        new_qty = item["quantity"] - 1
        if new_qty <= 0:
            await db.execute("DELETE FROM inventory WHERE user_id=? AND item_id=?", (user_id, item_id))
        else:
            await db.execute("UPDATE inventory SET quantity=? WHERE user_id=? AND item_id=?", (new_qty, user_id, item_id))
        await db.commit()
        return True, {"item": item, "effect": effect_text, "remaining": max(0, new_qty)}

async def get_inventory(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT i.item_id, i.quantity, s.name, s.description, s.category
               FROM inventory i JOIN shop_items s ON s.id=i.item_id
               WHERE i.user_id=? AND i.quantity>0 ORDER BY s.category, s.id""",
            (user_id,)
        )
        return await cur.fetchall()

async def add_gems(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET soul_gems=soul_gems+? WHERE user_id=?", (amount, user_id))
        await db.commit()

async def admin_add_shop_item(name, description, category, coins, gems, energy, bonus):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO shop_items
               (name, description, category, price_coins, price_gems, energy_gain, mission_bonus)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, description, category, coins, gems, energy, bonus)
        )
        await db.commit()
        return cur.lastrowid


async def search_users(term: str, limit=20):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        term = term.strip()
        if term.isdigit():
            cur = await db.execute(
                "SELECT * FROM users WHERE user_id=? LIMIT ?", (int(term), limit)
            )
        else:
            cur = await db.execute(
                "SELECT * FROM users WHERE name LIKE ? ORDER BY xp DESC LIMIT ?",
                (f"%{term}%", limit)
            )
        return await cur.fetchall()

async def get_full_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = await cur.fetchone()
        cur = await db.execute(
            "SELECT banned, ban_until, reason FROM moderation WHERE user_id=?",
            (user_id,)
        )
        moderation = await cur.fetchone()
        cur = await db.execute(
            "SELECT COUNT(*) AS c FROM warnings WHERE user_id=?", (user_id,)
        )
        warnings = await cur.fetchone()
        return user, moderation, warnings["c"] if warnings else 0

async def admin_update_user(user_id: int, coins=None, gems=None, health=None, energy=None, level=None):
    fields, values = [], []
    if coins is not None: fields += ["coins=coins+?"]; values += [coins]
    if gems is not None: fields += ["soul_gems=soul_gems+?"]; values += [gems]
    if health is not None: fields += ["health=?"]; values += [max(0, health)]
    if energy is not None: fields += ["energy=energy+?"]; values += [energy]
    if level is not None:
        fields += ["level=?", "xp=?"]
        values += [max(1, level), max(0, (level-1)*250)]
    if not fields: return
    values.append(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {', '.join(fields)} WHERE user_id=?", values)
        await db.commit()

async def add_warning(user_id: int, admin_id: int, reason: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO warnings(user_id, admin_id, reason) VALUES (?, ?, ?)",
            (user_id, admin_id, reason[:500])
        )
        await db.commit()

async def get_warnings(user_id: int, limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM warnings WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        return await cur.fetchall()

async def set_temporary_ban(user_id: int, until_iso: str, reason: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO moderation(user_id,banned,ban_until,reason)
               VALUES (?,1,?,?)
               ON CONFLICT(user_id) DO UPDATE SET banned=1, ban_until=excluded.ban_until, reason=excluded.reason""",
            (user_id, until_iso, reason[:500])
        )
        await db.commit()

async def clear_ban(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO moderation(user_id,banned,ban_until,reason)
               VALUES (?,0,NULL,NULL)
               ON CONFLICT(user_id) DO UPDATE SET banned=0, ban_until=NULL, reason=NULL""",
            (user_id,)
        )
        await db.commit()

async def get_inventory_for_admin(user_id: int):
    return await get_inventory(user_id)

async def add_admin_log(admin_id: int, action: str, target_id=None, details=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO admin_logs(admin_id, action, target_id, details) VALUES (?, ?, ?, ?)",
            (admin_id, action[:100], target_id, details[:1000])
        )
        await db.commit()

async def get_admin_logs(limit=30):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM admin_logs ORDER BY id DESC LIMIT ?", (limit,)
        )
        return await cur.fetchall()


async def list_regions():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory=aiosqlite.Row
        cur=await db.execute("SELECT * FROM regions WHERE active=1 ORDER BY unlock_level")
        return await cur.fetchall()

async def get_region(region_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory=aiosqlite.Row
        cur=await db.execute("SELECT * FROM regions WHERE id=? AND active=1",(region_id,)); return await cur.fetchone()

async def list_story_spirits(region_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory=aiosqlite.Row
        if region_id:
            cur=await db.execute("SELECT s.*,r.name region_name FROM spirits_story s JOIN regions r ON r.id=s.region_id WHERE s.active=1 AND s.region_id=? ORDER BY s.difficulty,s.id",(region_id,))
        else:
            cur=await db.execute("SELECT s.*,r.name region_name FROM spirits_story s JOIN regions r ON r.id=s.region_id WHERE s.active=1 ORDER BY s.difficulty,s.id")
        return await cur.fetchall()

async def get_story_spirit(sid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory=aiosqlite.Row
        cur=await db.execute("SELECT s.*,r.name region_name FROM spirits_story s JOIN regions r ON r.id=s.region_id WHERE s.id=? AND s.active=1",(sid,)); return await cur.fetchone()

async def get_spirit_progress(user_id,sid):
    async with aiosqlite.connect(DB_PATH) as db:
        cur=await db.execute("SELECT clue_index,status FROM spirit_progress WHERE user_id=? AND spirit_id=?",(user_id,sid)); return await cur.fetchone()

async def get_next_clue(user_id,sid):
    progress=await get_spirit_progress(user_id,sid); idx=progress[0] if progress else 0
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory=aiosqlite.Row
        cur=await db.execute("SELECT * FROM spirit_clues WHERE spirit_id=? ORDER BY clue_order LIMIT 1 OFFSET ?",(sid,idx)); return await cur.fetchone()

async def advance_spirit(user_id,sid,correct):
    async with aiosqlite.connect(DB_PATH) as db:
        cur=await db.execute("SELECT clue_index,status FROM spirit_progress WHERE user_id=? AND spirit_id=?",(user_id,sid)); row=await cur.fetchone(); idx=row[0] if row else 0
        if not correct: return False,idx,False
        idx+=1
        cur=await db.execute("SELECT COUNT(*) FROM spirit_clues WHERE spirit_id=?",(sid,)); total=(await cur.fetchone())[0]
        status='completed' if idx>=total else 'active'
        await db.execute("INSERT INTO spirit_progress(user_id,spirit_id,clue_index,status) VALUES (?,?,?,?) ON CONFLICT(user_id,spirit_id) DO UPDATE SET clue_index=excluded.clue_index,status=excluded.status",(user_id,sid,idx,status)); await db.commit()
        return True,idx,status=='completed'

async def list_demons(region_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory=aiosqlite.Row
        if region_id: cur=await db.execute("SELECT d.*,r.name region_name FROM demons d JOIN regions r ON r.id=d.region_id WHERE d.active=1 AND d.region_id=? ORDER BY d.rank,d.id",(region_id,))
        else: cur=await db.execute("SELECT d.*,r.name region_name FROM demons d JOIN regions r ON r.id=d.region_id WHERE d.active=1 ORDER BY d.rank,d.id")
        return await cur.fetchall()

async def get_demon(did):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory=aiosqlite.Row; cur=await db.execute("SELECT d.*,r.name region_name FROM demons d JOIN regions r ON r.id=d.region_id WHERE d.id=? AND d.active=1",(did,)); return await cur.fetchone()

async def get_or_create_encounter(user_id,did):
    d=await get_demon(did)
    if not d:return None
    async with aiosqlite.connect(DB_PATH) as db:
        cur=await db.execute("SELECT * FROM demon_encounters WHERE user_id=? AND demon_id=?",(user_id,did)); row=await cur.fetchone()
        if not row:
            await db.execute("INSERT INTO demon_encounters(user_id,demon_id,health,corruption,stage) VALUES (?,?,?,?,1)",(user_id,did,d['health'],d['corruption'])); await db.commit()
        cur=await db.execute("SELECT * FROM demon_encounters WHERE user_id=? AND demon_id=?",(user_id,did)); return await cur.fetchone()

async def update_encounter(user_id,did,health,corruption,stage,status='active'):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE demon_encounters SET health=?,corruption=?,stage=?,status=? WHERE user_id=? AND demon_id=?",(health,corruption,stage,status,user_id,did)); await db.commit()

async def add_light(user_id,amount):
    async with aiosqlite.connect(DB_PATH) as db:
        # SQLite creates the column migration lazily below if needed.
        await db.execute("UPDATE users SET light=light+? WHERE user_id=?",(amount,user_id)); await db.commit()


async def get_marriage(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM marriages WHERE (user1_id=? OR user2_id=?) AND status='accepted' ORDER BY id DESC LIMIT 1",
            (user_id, user_id)
        )
        return await cur.fetchone()

async def get_pending_proposal(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM marriages WHERE user2_id=? AND status='pending' ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
        return await cur.fetchone()

async def create_marriage_proposal(user1_id: int, user2_id: int):
    if user1_id == user2_id:
        return False, 'نمی‌توانی به خودت پیشنهاد ازدواج بدهی.'
    if not await get_user(user2_id):
        return False, 'بازیکن موردنظر پیدا نشد.'
    if await get_marriage(user1_id) or await get_marriage(user2_id):
        return False, 'یکی از شما در حال حاضر متأهل است.'
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM marriages WHERE ((user1_id=? AND user2_id=?) OR (user1_id=? AND user2_id=?)) AND status='pending'",
            (user1_id,user2_id,user2_id,user1_id)
        )
        if await cur.fetchone():
            return False, 'برای این بازیکن قبلاً پیشنهاد ثبت شده است.'
        await db.execute("INSERT INTO marriages(user1_id,user2_id,status) VALUES (?,?,?)", (user1_id,user2_id,'pending'))
        await db.commit()
    return True, 'پیشنهاد ازدواج ارسال شد.'

async def respond_marriage(proposal_id: int, user_id: int, accept: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM marriages WHERE id=? AND user2_id=? AND status='pending'", (proposal_id,user_id))
        row = await cur.fetchone()
        if not row:
            return False
        status='accepted' if accept else 'rejected'
        await db.execute("UPDATE marriages SET status=? WHERE id=?", (status,proposal_id))
        await db.commit()
        return True

async def list_children(user_id: int):
    marriage=await get_marriage(user_id)
    ids=[user_id]
    if marriage:
        partner=marriage['user2_id'] if marriage['user1_id']==user_id else marriage['user1_id']
        ids.append(partner)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory=aiosqlite.Row
        cur=await db.execute(
            "SELECT * FROM children WHERE parent1_id IN (?,?) OR parent2_id IN (?,?) ORDER BY id DESC",
            (ids[0],ids[1] if len(ids)>1 else ids[0],ids[0],ids[1] if len(ids)>1 else ids[0])
        )
        return await cur.fetchall()

async def adopt_child(user_id: int, name: str):
    name=name.strip()[:40]
    if not name:
        return False, 'نام کودک را وارد کن.'
    marriage=await get_marriage(user_id)
    parent2=None
    if marriage:
        parent2=marriage['user2_id'] if marriage['user1_id']==user_id else marriage['user1_id']
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO children(parent1_id,parent2_id,name) VALUES (?,?,?)", (user_id,parent2,name))
        await db.commit()
    return True, name

async def care_for_child(user_id: int, child_id: int):
    children=await list_children(user_id)
    allowed=any(c['id']==child_id for c in children)
    if not allowed:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE children SET happiness=MIN(100,happiness+10), health=MIN(100,health+5) WHERE id=?", (child_id,))
        await db.commit()
    return True


async def train_mind(user_id: int):
    """تمرین روزانه ذهن؛ یک بار در هر UTC day."""
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT energy, mind_power, training_points, last_training FROM users WHERE user_id=?", (user_id,))
        u = await cur.fetchone()
        if not u:
            return False, "کاربر پیدا نشد."
        if u["last_training"] == today:
            return False, "امروز تمرین ذهن را انجام داده‌ای. فردا دوباره امتحان کن."
        if u["energy"] < 2:
            return False, "برای تمرین ذهن حداقل ۲ انرژی لازم داری."
        gain = 1 + (u["training_points"] // 10)
        await db.execute("UPDATE users SET energy=energy-2, mind_power=mind_power+?, training_points=training_points+1, xp=xp+?, last_training=? WHERE user_id=?", (gain, 5 + gain, today, user_id))
        await db.commit()
        return True, gain

async def get_training_stats(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT mind_power, body_power, spirit_power, training_points FROM users WHERE user_id=?", (user_id,))
        return await cur.fetchone()
