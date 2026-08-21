import aiosqlite
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

# PostgreSQL connection string is provided through DATABASE_URL.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DB_PATH = DATABASE_URL  # kept for compatibility with game.py/web_app.py
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL در فایل .env تنظیم نشده است.")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
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
            user_id BIGINT NOT NULL,
            spirit_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            PRIMARY KEY(user_id, spirit_id)
        );

        CREATE TABLE IF NOT EXISTS staff (
            user_id BIGINT PRIMARY KEY,
            role TEXT NOT NULL DEFAULT 'ادمین',
            added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS moderation (
            user_id BIGINT PRIMARY KEY,
            banned INTEGER NOT NULL DEFAULT 0,
            ban_until TEXT,
            reason TEXT
        );

        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT NOT NULL,
            admin_id BIGINT NOT NULL,
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id BIGINT NOT NULL,
            action TEXT NOT NULL,
            target_id BIGINT,
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
            user_id BIGINT NOT NULL,
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
            user_id BIGINT NOT NULL, spirit_id INTEGER NOT NULL, clue_index INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'active',
            PRIMARY KEY(user_id, spirit_id)
        );

        CREATE TABLE IF NOT EXISTS demons (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, type TEXT NOT NULL, rank INTEGER NOT NULL DEFAULT 1,
            power INTEGER NOT NULL DEFAULT 50, defense INTEGER NOT NULL DEFAULT 20, health INTEGER NOT NULL DEFAULT 100, corruption INTEGER NOT NULL DEFAULT 100,
            temperament TEXT NOT NULL, ability TEXT NOT NULL, story TEXT NOT NULL, region_id INTEGER NOT NULL, reward_coins INTEGER NOT NULL DEFAULT 80, reward_xp INTEGER NOT NULL DEFAULT 50, active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS demon_encounters (
            user_id BIGINT NOT NULL, demon_id INTEGER NOT NULL, health INTEGER NOT NULL, corruption INTEGER NOT NULL, stage INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'active', PRIMARY KEY(user_id, demon_id)
        );

        CREATE TABLE IF NOT EXISTS currencies (
            key TEXT PRIMARY KEY, value INTEGER NOT NULL, description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS marriages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id BIGINT NOT NULL,
            user2_id BIGINT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user1_id, user2_id)
        );

        CREATE TABLE IF NOT EXISTS children (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent1_id BIGINT NOT NULL,
            parent2_id BIGINT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL DEFAULT 0,
            happiness INTEGER NOT NULL DEFAULT 80,
            health INTEGER NOT NULL DEFAULT 100,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_missions (
            user_id BIGINT NOT NULL,
            mission_key TEXT NOT NULL,
            day TEXT NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            claimed INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, mission_key, day)
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
                    ("کودک زنگوله",
                     "کودکی که زنگوله‌اش را گم کرده و دیگر نمی‌خندد.",
                     "زنگوله را پیدا کن و به او برگردان.",
                     1, 55, 30),
                    ("عروس بی‌داماد",
                     "روحی در لباس عروسی که هنوز منتظر کسی است که نیامد.",
                     "حقیقت آن شب را آشکار کن.",
                     2, 130, 85),
                    ("سرباز بی‌نام",
                     "سربازی که نامش از سنگ مزار پاک شده است.",
                     "نام واقعی‌اش را پیدا کن.",
                     3, 200, 130),
                    ("آشپز آشپزخانه خاموش",
                     "بوی غذا از آشپزخانه‌ای می‌آید که سال‌هاست خالی است.",
                     "دستور غذایی که نیمه‌کاره مانده را کامل کن.",
                     2, 120, 75),
                    ("کتابدار بی‌کتاب",
                     "روحی که بین قفسه‌های خالی هنوز کتاب جستجو می‌کند.",
                     "کتاب گمشده را پیدا کن.",
                     4, 280, 200),
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
                    ("🥣 آش شب‌زنده‌داری", "آش گرم برای شب‌های مأموریت طولانی.", "🍵 خوراکی", 120, 0, 6, 3, 1),
                    ("🍯 عسل جنگل مه", "عسل نادر از کندوهای جنگل مه‌آلود.", "🍵 خوراکی", 200, 1, 4, 10, 1),
                    ("🕯️ فانوس روح", "افزایش شانس موفقیت مأموریت.", "🧿 ابزار محافظ", 150, 0, 0, 8, 1),
                    ("🔮 مهر محافظ", "محافظی جادویی که به مأموریت بعدی کمک می‌کند.", "🧿 ابزار محافظ", 250, 1, 0, 15, 1),
                    ("🪞 آینه حقیقت", "دروغ سرنخ‌های اشتباه را کمی آشکارتر می‌کند.", "🧿 ابزار محافظ", 320, 2, 0, 12, 1),
                    ("📿 تسبیح نور", "نور پسین را در مأموریت‌های سخت پایدار نگه می‌دارد.", "🧿 ابزار محافظ", 280, 1, 0, 10, 1),
                    ("⚡ انرژی روحی", "بسته انرژی برای محافظ.", "⚡ انرژی", 60, 0, 10, 0, 1),
                    ("⚡⚡ بسته انرژی بزرگ", "انرژی زیاد برای مأموریت‌های پیاپی.", "⚡ انرژی", 150, 1, 25, 0, 1),
                    ("📜 طومار احضار", "یک مأموریت ویژه به دفتر ارواح اضافه می‌کند.", "📜 مأموریتی", 400, 3, 0, 20, 1),
                    ("📜 طومار پاک‌سازی", "قدرت روح را برای مقابله با جن تقویت می‌کند.", "📜 مأموریتی", 350, 2, 0, 18, 1),
                    ("🎁 جعبه اسرار", "یک آیتم تصادفی از فروشگاه.", "💎 ویژه", 500, 5, 0, 10, 1),
                    ("🎁 جعبه نور پسین", "شانس دریافت کریستال یا نور پسین بیشتر.", "💎 ویژه", 700, 8, 0, 15, 1),
                ]
            )

        # PostgreSQL migration: Telegram IDs can exceed a signed 32-bit integer.
        # Keep all Telegram/user identifiers as BIGINT.
        for statement in [
            "ALTER TABLE users ALTER COLUMN user_id TYPE BIGINT",
            "ALTER TABLE user_spirits ALTER COLUMN user_id TYPE BIGINT",
            "ALTER TABLE staff ALTER COLUMN user_id TYPE BIGINT",
            "ALTER TABLE moderation ALTER COLUMN user_id TYPE BIGINT",
            "ALTER TABLE warnings ALTER COLUMN user_id TYPE BIGINT",
            "ALTER TABLE warnings ALTER COLUMN admin_id TYPE BIGINT",
            "ALTER TABLE admin_logs ALTER COLUMN admin_id TYPE BIGINT",
            "ALTER TABLE admin_logs ALTER COLUMN target_id TYPE BIGINT",
            "ALTER TABLE inventory ALTER COLUMN user_id TYPE BIGINT",
            "ALTER TABLE spirit_progress ALTER COLUMN user_id TYPE BIGINT",
            "ALTER TABLE demon_encounters ALTER COLUMN user_id TYPE BIGINT",
            "ALTER TABLE marriages ALTER COLUMN user1_id TYPE BIGINT",
            "ALTER TABLE marriages ALTER COLUMN user2_id TYPE BIGINT",
            "ALTER TABLE children ALTER COLUMN parent1_id TYPE BIGINT",
            "ALTER TABLE children ALTER COLUMN parent2_id TYPE BIGINT",
        ]:
            try:
                await db.execute(statement)
            except Exception:
                pass

        # Migration for existing databases.
        for statement in [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS max_health INTEGER NOT NULL DEFAULT 100",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS health INTEGER NOT NULL DEFAULT 100",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS light INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS gender TEXT",
            "ALTER TABLE moderation ADD COLUMN IF NOT EXISTS ban_until TEXT",
            "ALTER TABLE moderation ADD COLUMN IF NOT EXISTS reason TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS mind_power INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS body_power INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS spirit_power INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS training_points INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_training TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS coin_boost INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS deaths INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS dead_until TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS hunger INTEGER NOT NULL DEFAULT 100",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS thirst INTEGER NOT NULL DEFAULT 100",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_needs TEXT",
            "ALTER TABLE shop_items ADD COLUMN IF NOT EXISTS health_gain INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE shop_items ADD COLUMN IF NOT EXISTS hunger_gain INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE shop_items ADD COLUMN IF NOT EXISTS thirst_gain INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE spirit_progress ADD COLUMN IF NOT EXISTS mistakes INTEGER NOT NULL DEFAULT 0",
            """CREATE TABLE IF NOT EXISTS season_scores (
                user_id BIGINT NOT NULL,
                season_id TEXT NOT NULL,
                points INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, season_id)
            )""",
            """CREATE TABLE IF NOT EXISTS player_chat (
                id INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                from_id BIGINT NOT NULL,
                to_id BIGINT NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""",
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
                ("🌲 جنگل مه‌آلود","جنگلی که صداهای ناشناخته در مه آن می‌پیچد.",8),
                ("🏙️ شهر خاموش","شهری که مردمش رازهای زیادی را پنهان کرده‌اند.",15),
                ("🪦 گورستان قدیمی","محل تجمع روح‌های خشمگین و پرونده‌های دشوار.",25),
                ("🏰 عمارت فراموش‌شده","عمارت متروکه با یک راز قدیمی.",35),
                ("🌊 دهکده غرق‌شده","بخشی از روستا زیر آب مانده و داستانش تمام نشده است.",50),
                ("🌑 سرزمین سایه‌ها","مرزی میان جهان انسان‌ها و موجودات سایه‌ای.",70),
                ("🚪 دروازه دنیای پسین","آخرین مرز راهنمایان ارواح.",100),
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
                ("زوزه‌گر مه","جن جنگلی",2,110,40,280,65,"وحشی","زوزه ترس","در مه جنگل ظاهر می‌شود و مسیر را گم می‌کند.",2,170,115),
                ("اشک‌خور","روح آلوده",4,180,70,520,88,"غمگین","بلعیدن خاطره","از غم انسان‌ها تغذیه می‌کند و خاطرات را می‌دزدد.",3,320,220),
                ("مهره‌دار دروازه","نگهبان باستانی",6,300,120,1100,98,"سنگین","قفل ابدی","از دروازه دنیای پسین محافظت می‌کند و تنها با نور پسین ضعیف می‌شود.",8,900,650),
                ("سوت‌زن کوچه","جن شهری",1,60,25,150,50,"شیطنت‌آمیز","سوت گمراه‌کننده","در کوچه‌های روستای متروکه سوت می‌زند و کودکان را به بن‌بست می‌کشاند.",1,90,55),
                ("ریشه‌پیچ","موجود جنگلی",3,130,50,380,75,"کند","ریشه در پا","ریشه‌هایش را دور پای مسافران می‌پیچد تا در مه گیر کنند.",2,210,145),
                ("آینه‌شکن","روح آلوده",3,150,45,400,80,"پارانویا","تکثیر سایه","هر آینه‌ای که ببیند، نسخه‌ای از خودش می‌سازد.",3,260,180),
                ("خاک‌خور قبر","موجود گورستانی",4,200,80,600,90,"گرسنه","بلعیدن استخوان","زیر سنگ‌قبرها زندگی می‌کند و از آرامش مردگان تغذیه می‌کند.",4,380,260),
                ("شمع‌کش عمارت","جن خانگی",4,170,65,480,82,"وسواسی","خاموشی نور","شمع‌ها و فانوس‌ها را یکی‌یکی خاموش می‌کند تا تاریکی کامل شود.",5,350,240),
                ("موج‌دزد","موجود آبی",5,220,90,700,92,"بی‌رحم","کشیدن به عمق","از دهکده غرق‌شده بیرون می‌آید و قایق‌ها را به عمق می‌کشد.",6,520,380),
                ("پژواک دروغ","سایه ذهنی",5,240,85,750,94,"فریبنده","پژواک خاطره جعلی","خاطرات جعلی در ذهن قربانی تکرار می‌کند تا حقیقت را گم کند.",7,580,420),
                ("دروازه‌بان نهایی","نگهبان ابدی",7,350,140,1400,99,"قاطع","قفل دو جهان","آخرین نگهبان؛ فقط محافظان با نور پسین بالا می‌توانند او را آرام کنند.",8,1200,900),
            ])
        cur=await db.execute("SELECT COUNT(*) FROM currencies")
        if (await cur.fetchone())[0] == 0:
            await db.executemany("INSERT INTO currencies(key,value,description) VALUES (?,?,?)", [
                ("starting_coins",100,"سکه شروع"),("starting_energy",10,"انرژی شروع"),("starting_gems",0,"کریستال شروع"),("starting_light",0,"نور پسین"),
                ("daily_coins",100,"پاداش روزانه سکه"),("daily_energy",5,"پاداش روزانه انرژی")
            ])

        # داستان‌های جدید — INSERT شرطی تا با دیتابیس قدیمی هم اضافه شوند.
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
            # —— محتوای جدید ——
            ("چراغ خانهٔ خالی", 54, "روح سرگردان", 1, 1, "سرگردان",
             "روشن کردن چراغی که هر شب خودش خاموش می‌شود.",
             "در روستای متروکه، خانه‌ای هست که چراغش هر شب روشن می‌شود و تا سحر خاموش است. کسی داخل خانه نیست؛ اما رد انگشت روی شیشه تازه است.", 100, 70),
            ("سگ وفادار", 0, "روح حیوان", 1, 2, "سرگردان",
             "پیدا کردن صاحب سگی که هنوز جلوی در خانه منتظر است.",
             "سگی شفاف هر غروب جلوی خانه‌ای می‌نشیند و به جاده خیره می‌شود. اگر نزدیک شوی، به سمت گورستان قدیمی پارس می‌کند.", 150, 100),
            ("نقاش نیمه‌کاره", 38, "روح هنرمند", 2, 3, "سرگردان",
             "کامل کردن تابلویی که چهرهٔ سوژه‌اش محو شده است.",
             "در جنگل مه‌آلود، سه پایهٔ نقاشی با تابلویی ناتمام پیدا می‌شود. هر بار که رنگ می‌زنی، چهرهٔ دیگری ظاهر می‌شود.", 280, 190),
            ("فروشندهٔ ساعت‌های شکسته", 51, "روح تاجر", 3, 3, "سرگردان",
             "پیدا کردن ساعتی که هنوز کار می‌کند.",
             "در شهر خاموش، مغازه‌ای پر از ساعت‌های ازکارافتاده است. فروشنده فقط یک جمله می‌گوید: «زمان برای یکی از شما هنوز نرسیده.»", 300, 210),
            ("قبری بدون نام", 0, "روح بی‌هویت", 4, 4, "سرگردان",
             "نوشتن نام درست روی سنگ مزار.",
             "در گورستان، قبری هست که هر بار نامی متفاوت روی آن دیده می‌شود. گل‌های تازه هر صبح آنجا گذاشته می‌شوند؛ اما کسی دیده نشده.", 400, 280),
            ("نوازندهٔ عمارت", 29, "روح موسیقیدان", 5, 4, "سرگردان",
             "پیدا کردن نت گمشدهٔ قطعهٔ ناتمام.",
             "از طبقهٔ بالای عمارت فراموش‌شده صدای پیانو می‌آید. قطعه همیشه در یک نت متوقف می‌شود؛ انگار نوازنده منتظر کسی است که آن نت را بداند.", 450, 320),
            ("ماهیگیر بی‌تور", 67, "روح غرق‌شده", 6, 5, "سرگردان",
             "پیدا کردن چیزی که از تور او افتاده بود.",
             "کنار اسکلهٔ نیمه‌غرق، پیرمردی هر شب تور می‌اندازد؛ اما تور همیشه خالی بالا می‌آید. می‌گوید یک‌بار چیزی گرفت که نباید می‌گرفت.", 550, 400),
            ("کتاب قوانین سایه‌ها", 102, "روح کتابدار", 7, 6, "سرگردان",
             "یافتن صفحه‌ای که از کتاب قوانین پاره شده است.",
             "در سرزمین سایه‌ها، کتابی هست که قوانین عبور از مرز دو جهان را نوشته. یک صفحه پاره شده و بدون آن هیچ روحی نمی‌تواند آرام بگیرد.", 800, 600),
            ("آخرین راهنما", 120, "روح راهنما", 8, 8, "سرگردان",
             "تحویل مشعل نور پسین به نگهبان دروازه.",
             "در دروازهٔ دنیای پسین، روحی ایستاده که خودش زمانی راهنمای ارواح بوده. مشعلش خاموش شده و می‌گوید فقط یک محافظ واقعی می‌تواند آن را دوباره روشن کند.", 1500, 1100),
            ("آینهٔ دوقلوها", 22, "روح دوقلو", 3, 4, "سرگردان",
             "تشخیص اینکه کدام تصویر در آینه حقیقت است.",
             "دو خواهر دوقلو در یک خانه زندگی می‌کردند. بعد از حادثه، فقط یکی مانده؛ اما آینه هنوز هر دو را نشان می‌دهد و هر کدام ادعا می‌کند زنده است.", 380, 270),
            ("نامهٔ سوخته", 45, "روح پشیمان", 1, 2, "سرگردان",
             "بازیابی متن نامه‌ای که در آتش سوخته است.",
             "بوی کاغذ سوخته از شومینهٔ خانهٔ متروکه می‌آید. روحی کنار آتش نشسته و می‌گوید اگر آن نامه خوانده می‌شد، هیچ‌کس نمی‌مرد.", 170, 115),
            ("ساعت شنی بی‌شن", 90, "روح زمان", 7, 6, "سرگردان",
             "پیدا کردن شن‌های گمشدهٔ ساعت.",
             "ساعت شنی بزرگی در سرزمین سایه‌ها ایستاده؛ اما شن داخل آن نیست. هر بار که نزدیک می‌شوی، چند ثانیه از حافظه‌ات پاک می‌شود.", 850, 640),
            # —— بسته محتوای روایی ——
            ("عروسک چشم‌دوزی", 9, "روح کودک", 1, 2, "سرگردان",
             "دوختن دوبارهٔ چشم عروسکی که شب‌ها می‌گرید.",
             "در اتاق زیرشیروانی روستای متروکه، عروسکی با چشم‌های کنده نشسته است. اگر نزدیک شوی، نجوا می‌کند: «مادرم گفت برمی‌گردد.»", 180, 120),
            ("پستچی هرگزنیامده", 41, "روح سرگردان", 1, 3, "سرگردان",
             "تحویل نامه‌ای که چهل سال در کیف پست مانده.",
             "کیف چرمی پستچی کنار جاده پیدا می‌شود. داخلش فقط یک نامه است؛ آدرس گیرنده همان خانه‌ای است که امشب چراغش روشن شد.", 220, 150),
            ("گم‌شده در مه سبزفام", 33, "روح جنگلی", 2, 3, "سرگردان",
             "یافتن مسیر خانه‌ای که فقط در مه دیده می‌شود.",
             "شکارچی‌ای که وارد مه جنگل شد، دیگر برنگشت. رد پوتین‌هایش ناگهان قطع می‌شود و به‌جای آن رد پای برهنه دیده می‌شود.", 300, 200),
            ("زنگ مدرسهٔ متروکه", 12, "روح دانش‌آموز", 3, 3, "سرگردان",
             "پیدا کردن دفتر نمره‌ای که نام یک نفر در آن خط خورده.",
             "هر صبح زنگ مدرسه‌ای که سال‌هاست بسته است به صدا درمی‌آید. روی نیمکت آخر، کولهٔ کوچکی با دفتر هنوز باز است.", 310, 210),
            ("عکاس شب‌های بارانی", 36, "روح هنرمند", 3, 4, "سرگردان",
             "ظاهر کردن عکسی که در تاریکخانه نیمه‌کاره مانده.",
             "تاریکخانهٔ زیر مغازه پر از عکس‌هایی است که چهره‌ها در آن محو شده‌اند. فقط یک نگاتیو هنوز ظاهر نشده؛ تاریخ رویش فرداست.", 400, 280),
            ("نگهبان بی‌شیفت", 58, "روح نگهبان", 4, 4, "سرگردان",
             "بستن دری که هر شب از داخل باز می‌شود.",
             "نگهبان گورستان می‌گوید هر شب صدای کلید از داخل اتاقک می‌آید؛ درحالی‌که کلید فقط پیش اوست.", 420, 300),
            ("شاهزادهٔ بی‌تاج", 17, "روح نجیب", 5, 5, "سرگردان",
             "یافتن تاجی که در آینه دیده می‌شود اما در اتاق نیست.",
             "در تالار عمارت، دختری با لباس مهمانی روی پله نشسته. می‌گوید تاجش را دیشب گذاشت روی میز؛ اما میز خالی است و فقط در آینه تاج می‌درخشد.", 500, 360),
            ("ناخدا بدون قطب‌نما", 71, "روح دریایی", 6, 5, "سرگردان",
             "بازگرداندن قطب‌نمایی که همیشه به سمت خانه اشاره می‌کند.",
             "روی موج‌شکن، ناخدایی ایستاده که کشتی‌اش سال‌ها پیش غرق شد. قطب‌نمایش را گم کرده و می‌گوید بدون آن نمی‌تواند راه خانه را به ارواح سرگردان نشان دهد.", 580, 420),
            ("قاضی سکوت", 95, "روح داور", 7, 7, "سرگردان",
             "صدور حکم دربارهٔ روحی که هیچ خاطره‌ای ندارد.",
             "در دادگاه سایه‌ها، متهمی نشسته که نه نام دارد نه جرم. سه شاهد شهادت می‌دهند؛ اما هر شهادت، شاهد قبلی را بی‌اعتبار می‌کند.", 1000, 800),
            ("کلیدساز دروازه", 140, "روح صنعتگر", 8, 8, "سرگردان",
             "ساخت کلیدی که فقط یک‌بار می‌چرخد.",
             "پیرمردی کنار دروازه دنیای پسین نشسته و کلید می‌تراشد. می‌گوید همه کلیدها تقلبی‌اند مگر یکی؛ و آن یکی را فقط محافظی می‌سازد که یک روح را با انتخاب سخت راهی کرده باشد.", 1600, 1200),
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
            "چراغ خانهٔ خالی": [
                ("چراغ فقط وقتی روشن است که کسی به پنجره نزدیک نشود. چه چیزی را بررسی می‌کنی؟","🪟 پنجره"),
                ("روی شیشه رد انگشت کودکی دیده می‌شود.","🔎 رد انگشت"),
                ("زیر فرش، کلید کوچکی به شکل شعله پیدا می‌شود.","🔑 کلید شعله"),
            ],
            "سگ وفادار": [
                ("سگ به سمت جاده پارس می‌کند، اما ردپا به گورستان می‌رود.","🪦 دنبال ردپا"),
                ("روی قلاده نام نیمه‌پاک‌شده‌ای هست.","🏷️ خواندن قلاده"),
                ("کنار یک سنگ مزار، استخوان اسباب‌بازی سگ دفن شده.","🦴 کندن خاک"),
            ],
            "نقاش نیمه‌کاره": [
                ("رنگ‌ها روی پالت هنوز خیس‌اند؛ یعنی نقاش تازه رفته.","🎨 بررسی پالت"),
                ("در پس‌زمینهٔ تابلو، برجی کشیده شده که در جنگل واقعی نیست.","🗼 پیدا کردن برج"),
                ("چهرهٔ محوشده با یکی از ارواح جنگل شباهت دارد.","👻 مقایسه چهره"),
            ],
            "فروشندهٔ ساعت‌های شکسته": [
                ("فقط یک ساعت عقربه دارد که برعکس می‌چرخد.","🕰️ ساعت برعکس"),
                ("دفتر فروش نشان می‌دهد آخرین خریدار هرگز از مغازه بیرون نرفته.","📖 دفتر فروش"),
                ("پشت ویترین، عکسی از شهری است که هنوز ساخته نشده.","🏙️ عکس شهر"),
            ],
            "قبری بدون نام": [
                ("گل‌های تازه از گونه‌ای هستند که فقط در عمارت می‌رویند.","🌸 بررسی گل"),
                ("هر نام روی سنگ، با یک تاریخ مرگ متفاوت همراه است.","📅 مقایسه تاریخ‌ها"),
                ("زیر سنگ، لوحی با یک نام واقعی پنهان شده.","🪨 بلند کردن سنگ"),
            ],
            "نوازندهٔ عمارت": [
                ("پیانو روی یک نت خاص قفل شده است.","🎹 بررسی کلیدها"),
                ("در کشوی پیانو، نت‌نویسی با جوهر تازه هست.","📝 خواندن نت"),
                ("صدا از اتاقی می‌آید که در نقشه عمارت نیست.","🚪 پیدا کردن اتاق"),
            ],
            "ماهیگیر بی‌تور": [
                ("تور پاره است؛ چیزی سنگین آن را کشیده.","🕸️ بررسی تور"),
                ("روی اسکله، قلاب با علامت خانوادگی حک شده.","⚓ علامت قلاب"),
                ("زیر آب، جعبهٔ کوچکی به طناب بسته شده.","📦 کشیدن جعبه"),
            ],
            "کتاب قوانین سایه‌ها": [
                ("قفسه فقط وقتی باز می‌شود که نور پسین داشته باشی.","✨ نور پسین"),
                ("صفحهٔ پاره در حاشیهٔ کتاب‌های دیگر پنهان شده.","📚 جستجوی حاشیه"),
                ("قانون پاک‌شده دربارهٔ «راهنمای واقعی» صحبت می‌کند.","📜 خواندن قانون"),
            ],
            "آخرین راهنما": [
                ("مشعل فقط با نور پسین محافظ روشن می‌شود.","🕯️ نزدیک کردن نور"),
                ("نگهبان دروازه نام تو را از قبل می‌داند.","🗣️ گفتگو با نگهبان"),
                ("برای عبور، باید یک روح را شخصاً راهنمایی کرده باشی.","👻 اثبات راهنمایی"),
                ("آخرین آزمون: انتخاب بین قدرت و آرامش یک روح.","⚖️ انتخاب نهایی"),
            ],
            "آینهٔ دوقلوها": [
                ("در آینه، یکی از دوقلوها سایه ندارد.","🪞 بررسی سایه"),
                ("خاطرهٔ مشترک فقط در یکی از روایت‌ها با ساعت دیوار جور است.","🕰️ تطبیق زمان"),
                ("نام روی دستبند یکی از آن‌ها پاک شده است.","📿 بررسی دستبند"),
            ],
            "نامهٔ سوخته": [
                ("خاکستر نامه هنوز بوی جوهر می‌دهد.","💨 بوی خاکستر"),
                ("زیر شومینه، تکه کاغذی سالم مانده.","📄 تکه کاغذ"),
                ("نام گیرنده با یکی از اهالی روستا یکی است.","🗣️ پرس‌وجو از اهالی"),
            ],
            "ساعت شنی بی‌شن": [
                ("شن‌ها در سرزمین سایه‌ها به شکل ردپا پراکنده‌اند.","👣 دنبال ردپا"),
                ("هر بار نزدیک می‌شوی، یک خاطرهٔ کوتاه از دست می‌رود.","🧠 مراقبت از حافظه"),
                ("ظرف شنی در دست روحی است که زمان را می‌فروشد.","⏳ مذاکره با روح"),
            ],
            "عروسک چشم‌دوزی": [
                ("نخ و سوزن روی زمین افتاده؛ انگار کسی عجله داشته.","🧵 برداشتن نخ"),
                ("زیر تخت، جعبهٔ پارچه‌ای با چشم‌های شیشه‌ای هست.","📦 باز کردن جعبه"),
                ("عروسک وقتی چشم جدید می‌گیرد، نام مادر را نجوا می‌کند.","👻 گوش دادن به نجوا"),
            ],
            "پستچی هرگزنیامده": [
                ("مهر پست روی نامه تاریخ چهل سال پیش را دارد.","📮 بررسی مهر"),
                ("آدرس روی پاکت با چراغ روشن خانه یکی است.","🏮 دنبال چراغ"),
                ("گیرنده همان روحی است که هنوز منتظر خبر است.","🗣️ تحویل نامه"),
            ],
            "گم‌شده در مه سبزفام": [
                ("رد پوتین ناگهان به رد پای برهنه تبدیل می‌شود.","👣 مقایسه ردپا"),
                ("روی پوست درخت، علامت شکارچی حک شده.","🌳 خواندن علامت"),
                ("خانهٔ مه فقط وقتی دیده می‌شود که فانوس خاموش باشد.","🕯️ خاموش کردن فانوس"),
            ],
            "زنگ مدرسهٔ متروکه": [
                ("دفتر باز روی نیمکت، یک نام خط‌خورده دارد.","📖 خواندن دفتر"),
                ("کوله هنوز بوی نان تازه می‌دهد.","🎒 بررسی کوله"),
                ("زنگ از اتاق مدیر به صدا درمی‌آید؛ نه از حیاط.","🔔 دنبال صدا"),
            ],
            "عکاس شب‌های بارانی": [
                ("نگاتیو هنوز در مایع ظاهرکننده شناور است.","🧪 خارج کردن نگاتیو"),
                ("روی عکس نیمه‌ظاهر، چهره‌ای آشنا از شهر خاموش دیده می‌شود.","🖼️ دقیق شدن به چهره"),
                ("تاریخ روی حاشیه، فردای تقویم دیوار است.","📅 تطبیق تاریخ"),
            ],
            "نگهبان بی‌شیفت": [
                ("قفل از داخل خراش برداشته؛ انگار کسی بیرون رفته.","🔒 بررسی قفل"),
                ("کلید یدکی زیر پادری پیدا می‌شود.","🗝️ پیدا کردن کلید"),
                ("دفتر شیفت نشان می‌دهد یک نگهبان هرگز نامش ثبت نشده.","📋 دفتر شیفت"),
            ],
            "شاهزادهٔ بی‌تاج": [
                ("در آینه تاج می‌درخشد؛ روی میز چیزی نیست.","🪞 بررسی آینه"),
                ("پشت آینه، محفظهٔ مخفی با جواهر تقلبی هست.","💎 محفظه مخفی"),
                ("تاج واقعی در خاطرهٔ یک خدمتکار پنهان شده.","🗣️ گفتگو با خدمتکار"),
            ],
            "ناخدا بدون قطب‌نما": [
                ("قطب‌نما در شن‌های اسکله نصفه‌فرو رفته.","🧭 کندن شن"),
                ("عقربه همیشه به سمت خانه‌ای در دهکده اشاره می‌کند.","🏠 دنبال جهت"),
                ("با برگرداندن قطب‌نما، چند روح دیگر هم مسیر می‌گیرند.","⚓ راهنمایی گروهی"),
            ],
            "قاضی سکوت": [
                ("متهم هیچ خاطره‌ای ندارد؛ فقط یک کلید سنگی در دستش است.","🔑 بررسی کلید"),
                ("شاهد اول دروغ می‌گوید چون زمان واقعه را اشتباه می‌گوید.","⚖️ رد شهادت اول"),
                ("شاهد سوم همان روحی است که کلید را ساخته.","🔍 هویت شاهد سوم"),
                ("حکم درست: متهم قربانی است نه مجرم.","📜 صدور حکم"),
            ],
            "کلیدساز دروازه": [
                ("فلز کلید فقط با نور پسین ذوب می‌شود.","✨ ذوب با نور"),
                ("قالب کلید شبیه انتخاب سخت یک پروندهٔ قدیمی است.","⚖️ یادآوری انتخاب"),
                ("کلید یک‌بارمصرف است؛ باید بدانی برای کدام در است.","🚪 انتخاب دروازه"),
                ("آخرین ضربهٔ چکش، نام تو را روی دسته حک می‌کند.","🔨 تکمیل کلید"),
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

        # سخت‌تر کردن سطح باز شدن مناطق برای دیتابیس‌های قدیمی
        for name, lvl in [
            ("🌲 جنگل مه‌آلود", 8), ("🏙️ شهر خاموش", 15), ("🪦 گورستان قدیمی", 25),
            ("🏰 عمارت فراموش‌شده", 35), ("🌊 دهکده غرق‌شده", 50),
            ("🌑 سرزمین سایه‌ها", 70), ("🚪 دروازه دنیای پسین", 100),
        ]:
            try:
                await db.execute(
                    "UPDATE regions SET unlock_level=? WHERE name=?", (lvl, name)
                )
            except Exception:
                pass

        # جن‌های اضافه برای دیتابیس‌های موجود
        extra_demons = [
            ("سوت‌زن کوچه","جن شهری",1,60,25,150,50,"شیطنت‌آمیز","سوت گمراه‌کننده","در کوچه‌های روستای متروکه سوت می‌زند و کودکان را به بن‌بست می‌کشاند.",1,90,55),
            ("ریشه‌پیچ","موجود جنگلی",3,130,50,380,75,"کند","ریشه در پا","ریشه‌هایش را دور پای مسافران می‌پیچد تا در مه گیر کنند.",2,210,145),
            ("آینه‌شکن","روح آلوده",3,150,45,400,80,"پارانویا","تکثیر سایه","هر آینه‌ای که ببیند، نسخه‌ای از خودش می‌سازد.",3,260,180),
            ("خاک‌خور قبر","موجود گورستانی",4,200,80,600,90,"گرسنه","بلعیدن استخوان","زیر سنگ‌قبرها زندگی می‌کند و از آرامش مردگان تغذیه می‌کند.",4,380,260),
            ("شمع‌کش عمارت","جن خانگی",4,170,65,480,82,"وسواسی","خاموشی نور","شمع‌ها و فانوس‌ها را یکی‌یکی خاموش می‌کند تا تاریکی کامل شود.",5,350,240),
            ("موج‌دزد","موجود آبی",5,220,90,700,92,"بی‌رحم","کشیدن به عمق","از دهکده غرق‌شده بیرون می‌آید و قایق‌ها را به عمق می‌کشد.",6,520,380),
            ("پژواک دروغ","سایه ذهنی",5,240,85,750,94,"فریبنده","پژواک خاطره جعلی","خاطرات جعلی در ذهن قربانی تکرار می‌کند تا حقیقت را گم کند.",7,580,420),
            ("دروازه‌بان نهایی","نگهبان ابدی",7,350,140,1400,99,"قاطع","قفل دو جهان","آخرین نگهبان؛ فقط محافظان با نور پسین بالا می‌توانند او را آرام کنند.",8,1200,900),
            ("گریه‌گر چاه","روح چاهی",2,100,38,260,68,"غمگین","پژواک گریه","از ته چاه روستا صدا می‌زند و کسانی را که خم می‌شوند پایین می‌کشد.",1,160,100),
            ("شاخ‌پیچ مه","جن جنگلی",3,145,52,400,78,"وحشی","درهم‌پیچیدن شاخه","شاخه‌های زنده را مثل طناب دور قربانی می‌پیچد.",2,230,160),
            ("سایه‌نویس","سایه ذهنی",4,190,60,500,86,"خالق","نوشتن ترس","ترس‌هایت را روی دیوار می‌نویسد تا واقعی شوند.",3,340,240),
            ("کفن‌دزد","موجود گورستانی",5,230,95,720,93,"حریص","دزدیدن کفن","کفن مردگان را می‌دزدد تا خود را شبیه انسان کند.",4,480,340),
            ("مهمان ناخوانده","جن خانگی",4,175,68,490,83,"مودب","پذیرایی اجباری","با احترام وارد می‌شود و تا میزبان را نبلعد، نمی‌رود.",5,360,250),
            ("گرداب بی‌صدا","موجود آبی",6,270,110,900,97,"ساکت","بلعیدن صدا","قبل از کشیدن قربانی به عمق، همه صداها را می‌بلعد.",6,700,500),
            ("آینه‌دار اعظم","سایه سلطنتی",6,290,115,950,97,"متکبر","تکثیر سلطنت","سپاهی از بازتاب‌های خودش می‌سازد.",7,780,560),
            ("قفل‌بان ابدی","نگهبان قفل",7,340,135,1300,99,"وفادار","قفل هفت‌لایه","هفت قفل روی دروازه؛ هر قفل یک آزمون جداست.",8,1100,820),
        ]
        for d in extra_demons:
            cur = await db.execute("SELECT id FROM demons WHERE name=?", (d[0],))
            if not await cur.fetchone():
                await db.execute(
                    """INSERT INTO demons
                    (name,type,rank,power,defense,health,corruption,temperament,ability,story,region_id,reward_coins,reward_xp)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", d)

        # آیتم‌های فروشگاه اضافه (با health_gain در صورت پشتیبانی ستون)
        extra_shop = [
            ("🥣 آش شب‌زنده‌داری", "آش گرم برای شب‌های مأموریت طولانی.", "🍵 خوراکی", 120, 0, 6, 3, 1),
            ("🍯 عسل جنگل مه", "عسل نادر از کندوهای جنگل مه‌آلود.", "🍵 خوراکی", 200, 1, 4, 10, 1),
            ("🪞 آینه حقیقت", "دروغ سرنخ‌های اشتباه را کمی آشکارتر می‌کند.", "🧿 ابزار محافظ", 320, 2, 0, 12, 1),
            ("📿 تسبیح نور", "نور پسین را در مأموریت‌های سخت پایدار نگه می‌دارد.", "🧿 ابزار محافظ", 280, 1, 0, 10, 1),
            ("⚡⚡ بسته انرژی بزرگ", "انرژی زیاد برای مأموریت‌های پیاپی.", "⚡ انرژی", 150, 1, 25, 0, 1),
            ("📜 طومار پاک‌سازی", "قدرت روح را برای مقابله با جن تقویت می‌کند.", "📜 مأموریتی", 350, 2, 0, 18, 1),
            ("🎁 جعبه نور پسین", "شانس دریافت کریستال یا نور پسین بیشتر.", "💎 ویژه", 700, 8, 0, 15, 1),
            ("💊 معجون شفا", "۲۵ واحد سلامتی بازیابی می‌کند.", "❤️ شفا", 180, 0, 0, 0, 1),
            ("🩹 باند روح", "۴۰ واحد سلامتی.", "❤️ شفا", 320, 1, 0, 0, 1),
            ("💉 سرم احیا", "۷۰ واحد سلامتی و خروج از مرگ.", "❤️ شفا", 500, 3, 5, 0, 1),
            ("❤️ قلب نورانی", "پر کردن کامل سلامتی.", "❤️ شفا", 900, 6, 0, 0, 1),
        ]
        for item in extra_shop:
            cur = await db.execute("SELECT id FROM shop_items WHERE name=?", (item[0],))
            if not await cur.fetchone():
                await db.execute(
                    """INSERT INTO shop_items
                    (name, description, category, price_coins, price_gems, energy_gain, mission_bonus, quantity)
                    VALUES (?,?,?,?,?,?,?,?)""", item)
        # تنظیم health_gain برای آیتم‌های شفا
        for name, hg in [
            ("💊 معجون شفا", 25), ("🩹 باند روح", 40), ("💉 سرم احیا", 70), ("❤️ قلب نورانی", 999),
        ]:
            try:
                await db.execute(
                    "UPDATE shop_items SET health_gain=? WHERE name=?", (hg, name)
                )
            except Exception:
                pass

        # خوراکی و نوشیدنی برای گرسنگی / تشنگی
        food_drink = [
            ("🍞 نان روستایی", "نان تازه از تنور روستا — سیرکننده.", "🍞 خوراکی", 45, 0, 2, 0, 1, 35, 5),
            ("🧀 پنیر کهنه", "پنیر تند برای سفرهای طولانی.", "🍞 خوراکی", 80, 0, 1, 0, 1, 50, 0),
            ("🍖 خوراک نگهبان", "وعده کامل برای محافظان خسته.", "🍞 خوراکی", 150, 0, 3, 0, 1, 70, 15),
            ("🍲 خورش روح‌افزا", "خورش گرم با سبزی جنگل.", "🍞 خوراکی", 220, 1, 4, 0, 1, 90, 20),
            ("💧 آب چشمه", "آب زلال چشمه روستا.", "💧 نوشیدنی", 30, 0, 1, 0, 1, 0, 40),
            ("🧃 شربت مه", "شربت خنک از گیاهان جنگل.", "💧 نوشیدنی", 70, 0, 2, 0, 1, 10, 60),
            ("🍵 چای آرام‌بخش", "چای برای رفع تشنگی و کمی انرژی.", "💧 نوشیدنی", 55, 0, 4, 0, 1, 5, 50),
            ("🥛 شیر ماه", "شیر نقره‌ای — سیر و سیراب.", "💧 نوشیدنی", 120, 1, 3, 0, 1, 30, 80),
        ]
        for item in food_drink:
            cur = await db.execute("SELECT id FROM shop_items WHERE name=?", (item[0],))
            if not await cur.fetchone():
                try:
                    await db.execute(
                        """INSERT INTO shop_items
                        (name, description, category, price_coins, price_gems, energy_gain, mission_bonus, quantity, hunger_gain, thirst_gain)
                        VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        item,
                    )
                except Exception:
                    await db.execute(
                        """INSERT INTO shop_items
                        (name, description, category, price_coins, price_gems, energy_gain, mission_bonus, quantity)
                        VALUES (?,?,?,?,?,?,?,?)""",
                        item[:8],
                    )
            try:
                await db.execute(
                    "UPDATE shop_items SET hunger_gain=?, thirst_gain=? WHERE name=?",
                    (item[8], item[9], item[0]),
                )
            except Exception:
                pass
        for name, hg, tg in [
            ("🥣 آش شب‌زنده‌داری", 40, 10), ("🍯 عسل جنگل مه", 25, 5),
            ("🍵 چای روحانی", 15, 20), ("🫖 چای مخصوص نگهبان", 20, 25),
            ("🍖 کباب روحانی", 45, 5), ("🍢 کباب ویژه محافظ", 55, 10),
        ]:
            try:
                await db.execute(
                    "UPDATE shop_items SET hunger_gain=?, thirst_gain=? WHERE name=?",
                    (hg, tg, name),
                )
            except Exception:
                pass

        await db.commit()

async def ensure_user(user_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users(user_id, name, coins, energy, soul_gems)
               VALUES (?, ?, COALESCE((SELECT value FROM currencies WHERE key='starting_coins'),100),
                          COALESCE((SELECT value FROM currencies WHERE key='starting_energy'),10),
                          COALESCE((SELECT value FROM currencies WHERE key='starting_gems'),0))
               ON CONFLICT(user_id) DO UPDATE SET name=EXCLUDED.name""",
            (user_id, name[:80])
        )
        await db.commit()
    try:
        await tick_needs(user_id)
    except Exception:
        pass


async def tick_needs(user_id: int):
    """کاهش تدریجی گرسنگی/تشنگی با گذر زمان (هر ۳۰ دقیقه حدود ۸ واحد)."""
    now = datetime.now(timezone.utc)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT hunger, thirst, last_needs FROM users WHERE user_id=?", (user_id,)
        )
        row = await cur.fetchone()
        if not row:
            return
        hunger = int(row["hunger"] if row["hunger"] is not None else 100)
        thirst = int(row["thirst"] if row["thirst"] is not None else 100)
        last = row["last_needs"]
        minutes = 30
        if last:
            try:
                last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                minutes = max(0, int((now - last_dt).total_seconds() // 60))
            except Exception:
                minutes = 0
        if minutes < 15 and last:
            return
        # هر ۱۵ دقیقه: -4 گرسنگی، -5 تشنگی
        steps = max(1, minutes // 15) if last else 0
        if steps <= 0 and last:
            return
        if not last:
            steps = 0
        hunger = max(0, hunger - steps * 4)
        thirst = max(0, thirst - steps * 5)
        await db.execute(
            "UPDATE users SET hunger=?, thirst=?, last_needs=? WHERE user_id=?",
            (hunger, thirst, now.isoformat(), user_id),
        )
        await db.commit()


async def apply_activity_needs(user_id: int, hunger_cost: int = 5, thirst_cost: int = 4):
    """مصرف گرسنگی/تشنگی هنگام مأموریت. اگر خیلی پایین باشد False."""
    await tick_needs(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT hunger, thirst FROM users WHERE user_id=?", (user_id,)
        )
        row = await cur.fetchone()
        if not row:
            return False, "کاربر پیدا نشد."
        h = int(row["hunger"] if row["hunger"] is not None else 100)
        t = int(row["thirst"] if row["thirst"] is not None else 100)
        if h < 10:
            return False, "🍗 خیلی گرسنه‌ای! از فروشگاه خوراکی بخر و استفاده کن."
        if t < 10:
            return False, "💧 خیلی تشنه‌ای! یک نوشیدنی از فروشگاه بنوش."
        await db.execute(
            "UPDATE users SET hunger=GREATEST(0, hunger-?), thirst=GREATEST(0, thirst-?) WHERE user_id=?",
            (hunger_cost, thirst_cost, user_id),
        )
        await db.commit()
    return True, ""

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

async def add_progress(user_id: int, coins: int, xp: int, spirit: bool = False, cleanse: bool = False, gems: int = 0):
    """اضافه کردن پاداش با در نظر گرفتن ارتقای سکه (coin_boost) و کریستال."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT coin_boost FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        boost = int(row["coin_boost"] or 0) if row else 0
        # هر سطح ارتقا ۵٪ سکه بیشتر (حداکثر +۵۰٪)
        bonus_pct = min(boost * 5, 50)
        final_coins = int(coins * (100 + bonus_pct) / 100)
        gems = max(0, int(gems or 0))
        await db.execute(
            """UPDATE users SET coins=coins+?, xp=xp+?, soul_gems=soul_gems+?,
               spirits_sent=spirits_sent+?, cleanses=cleanses+?
               WHERE user_id=?""",
            (final_coins, xp, gems, int(spirit), int(cleanse), user_id)
        )
        await db.execute(
            """UPDATE users SET level = 1 + CAST(xp / 250 AS INTEGER)
               WHERE user_id=?""", (user_id,)
        )
        await db.commit()
        # پیشرفت مأموریت‌های روزانه کریستال + امتیاز فصل
        try:
            if spirit:
                await _bump_mission(user_id, "spirit", 1)
                await add_season_points(user_id, max(1, xp // 20 + gems))
            if cleanse:
                await _bump_mission(user_id, "cleanse", 1)
                await add_season_points(user_id, max(1, xp // 15 + gems))
        except Exception:
            pass
        return final_coins, gems

async def upgrade_coin_boost(user_id: int):
    """
    ارتقای سطح سکه با هزینه تصاعدی سکه و کریستال.
    سطح ۰→۱: 500 سکه + 2 کریستال
    هر سطح بعدی هزینه ×۱.۶ و +۱ کریستال بیشتر.
    حداکثر سطح ۱۰ (+۵۰٪ پاداش سکه).
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT coins, soul_gems, coin_boost FROM users WHERE user_id=?", (user_id,)
        )
        row = await cur.fetchone()
        if not row:
            return False, "کاربر پیدا نشد."
        level = int(row["coin_boost"] or 0)
        if level >= 10:
            return False, "ارتقای سکه به حداکثر سطح (۱۰) رسیده است. (+۵۰٪ پاداش)"
        cost_coins = int(500 * (1.6 ** level))
        cost_gems = 2 + level
        if row["coins"] < cost_coins or row["soul_gems"] < cost_gems:
            return False, (
                f"منابع کافی نیست.\n"
                f"نیاز: 🪙 {cost_coins} سکه + 🔮 {cost_gems} کریستال\n"
                f"موجودی: 🪙 {row['coins']} | 🔮 {row['soul_gems']}"
            )
        new_level = level + 1
        await db.execute(
            "UPDATE users SET coins=coins-?, soul_gems=soul_gems-?, coin_boost=? WHERE user_id=?",
            (cost_coins, cost_gems, new_level, user_id)
        )
        await db.commit()
        bonus = min(new_level * 5, 50)
        return True, (
            f"✅ کیف پول ارتقا یافت!\n"
            f"سطح ارتقا: {new_level}/10\n"
            f"پاداش سکه از این به بعد: +{bonus}٪\n"
            f"هزینه پرداخت‌شده: 🪙 {cost_coins} + 🔮 {cost_gems}"
        )

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

def _today_tehran() -> str:
    """تاریخ روز به وقت ایران — همیشه یکسان (حتی اگر zoneinfo نباشد)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Tehran")).date().isoformat()
    except Exception:
        # تهران ≈ UTC+3:30
        return (datetime.now(timezone.utc) + __import__("datetime").timedelta(hours=3, minutes=30)).date().isoformat()


# کلیدها با پیشوند m_ تا با سهمیه روزانه (limit_spirit) قاطی نشوند
DAILY_MISSIONS = {
    "m_spirit": ("👻 راهنمایی ۱ روح", 1, 2),
    "m_cleanse": ("😈 پاک‌سازی ۱ جن", 1, 2),
    "m_train": ("🧠 یک تمرین ذهن", 1, 1),
    "m_shop": ("🛒 یک خرید از فروشگاه", 1, 1),
    "m_daily": ("🎁 دریافت جایزه روزانه", 1, 1),
}

# نگاشت کلید قدیمی → جدید (برای دیتابیس‌های قبلی)
_MISSION_KEY_ALIASES = {
    "spirit": "m_spirit",
    "cleanse": "m_cleanse",
    "train": "m_train",
    "shop": "m_shop",
    "daily": "m_daily",
}


async def _ensure_missions_table(db):
    await db.execute(
        """CREATE TABLE IF NOT EXISTS user_missions (
            user_id BIGINT NOT NULL,
            mission_key TEXT NOT NULL,
            day TEXT NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            claimed INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, mission_key, day)
        )"""
    )


async def _bump_mission(user_id: int, mission_key: str, amount: int = 1):
    """افزایش پیشرفت مأموریت کریستال — هرگز claimed را ریست نمی‌کند."""
    mission_key = _MISSION_KEY_ALIASES.get(mission_key, mission_key)
    if mission_key not in DAILY_MISSIONS:
        return
    day = _today_tehran()
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await _ensure_missions_table(db)
            # فقط progress را زیاد کن؛ claimed دست نخورده بماند
            await db.execute(
                """INSERT INTO user_missions(user_id, mission_key, day, progress, claimed)
                   VALUES (?, ?, ?, ?, 0)
                   ON CONFLICT (user_id, mission_key, day)
                   DO UPDATE SET progress = user_missions.progress + EXCLUDED.progress""",
                (user_id, mission_key, day, int(amount)),
            )
            await db.commit()
    except Exception as e:
        # لاگ بدون بلعیدن بی‌صدا
        import logging
        logging.getLogger("spirit-bot").warning("bump_mission failed: %s", e)


async def get_daily_missions(user_id: int):
    """لیست مأموریت‌های امروز با پیشرفت و وضعیت دریافت پاداش."""
    day = _today_tehran()
    rows = {}
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await _ensure_missions_table(db)
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT mission_key, progress, claimed FROM user_missions WHERE user_id=? AND day=?",
                (user_id, day),
            )
            for r in await cur.fetchall():
                key = r["mission_key"]
                # پشتیبانی از کلیدهای قدیمی
                key = _MISSION_KEY_ALIASES.get(key, key)
                prev = rows.get(key)
                if prev:
                    rows[key] = {
                        "progress": max(int(prev["progress"]), int(r["progress"])),
                        "claimed": max(int(prev["claimed"]), int(r["claimed"])),
                    }
                else:
                    rows[key] = {"progress": int(r["progress"]), "claimed": int(r["claimed"])}
    except Exception as e:
        import logging
        logging.getLogger("spirit-bot").warning("get_daily_missions failed: %s", e)

    result = []
    for key, (title, target, reward) in DAILY_MISSIONS.items():
        row = rows.get(key) or {}
        progress = int(row.get("progress") or 0)
        claimed = int(row.get("claimed") or 0)
        result.append({
            "key": key,
            "title": title,
            "target": target,
            "reward_gems": reward,
            "progress": min(progress, target),
            "done": progress >= target,
            "claimed": bool(claimed),
            "day": day,
        })
    return result


async def claim_mission_reward(user_id: int, mission_key: str):
    """دریافت پاداش کریستال مأموریت روزانه."""
    mission_key = _MISSION_KEY_ALIASES.get(mission_key, mission_key)
    if mission_key not in DAILY_MISSIONS:
        return False, "مأموریت نامعتبر است."
    title, target, reward = DAILY_MISSIONS[mission_key]
    day = _today_tehran()
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await _ensure_missions_table(db)
            db.row_factory = aiosqlite.Row
            # جمع پیشرفت از کلید جدید و قدیمی
            old_key = {v: k for k, v in _MISSION_KEY_ALIASES.items()}.get(mission_key)
            keys = [mission_key] + ([old_key] if old_key else [])
            progress = 0
            claimed = 0
            for k in keys:
                cur = await db.execute(
                    "SELECT progress, claimed FROM user_missions WHERE user_id=? AND mission_key=? AND day=?",
                    (user_id, k, day),
                )
                row = await cur.fetchone()
                if row:
                    progress = max(progress, int(row["progress"] or 0))
                    claimed = max(claimed, int(row["claimed"] or 0))
            if progress < target:
                return False, "هنوز این مأموریت کامل نشده است."
            if claimed:
                return False, "پاداش این مأموریت را قبلاً گرفته‌ای."
            await db.execute(
                """INSERT INTO user_missions(user_id, mission_key, day, progress, claimed)
                   VALUES (?, ?, ?, ?, 1)
                   ON CONFLICT (user_id, mission_key, day)
                   DO UPDATE SET claimed = 1, progress = GREATEST(user_missions.progress, EXCLUDED.progress)""",
                (user_id, mission_key, day, progress),
            )
            await db.execute(
                "UPDATE users SET soul_gems=soul_gems+? WHERE user_id=?",
                (reward, user_id),
            )
            await db.commit()
    except Exception as e:
        import logging
        logging.getLogger("spirit-bot").warning("claim_mission failed: %s", e)
        return False, "خطا در ثبت پاداش. دوباره تلاش کن."
    return True, f"✅ {title}\n🔮 +{reward} کریستال سایه"


async def daily_claim(user_id: int):
    """پاداش روزانه بر اساس روز تقویمی تهران (نه UTC)."""
    today = _today_tehran()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT last_daily, coins, energy FROM users WHERE user_id=?", (user_id,)
        )
        row = await cur.fetchone()
        if not row:
            return False, "ابتدا /start بزن."
        if row["last_daily"] == today:
            return False, "پاداش امروز را قبلاً گرفته‌ای. فردا دوباره بیا."
        gems = 1
        await db.execute(
            """UPDATE users SET coins=coins+40, energy=energy+3, soul_gems=soul_gems+?,
               health=LEAST(max_health, health+15), last_daily=? WHERE user_id=?""",
            (gems, today, user_id),
        )
        await db.commit()
    try:
        await _bump_mission(user_id, "daily", 1)
    except Exception:
        pass
    return True, (
        "🎁 پاداش روزانه دریافت شد!\n"
        f"🪙 +40 سکه\n💠 +3 انرژی\n🔮 +{gems} کریستال\n❤️ +15 سلامتی"
    )

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
    """اگر کاربر مسدود باشد True برمی‌گرداند. در صورت خطای دیتابیس False (اجازه عبور)."""
    try:
        from datetime import datetime, timezone
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "SELECT banned, ban_until FROM moderation WHERE user_id=?", (user_id,)
            )
            row = await cur.fetchone()
            if not row or not row[0]:
                return False
            if row[1]:
                try:
                    if datetime.fromisoformat(str(row[1])) <= datetime.now(timezone.utc):
                        await db.execute(
                            "UPDATE moderation SET banned=0, ban_until=NULL WHERE user_id=?",
                            (user_id,),
                        )
                        await db.commit()
                        return False
                except (ValueError, TypeError):
                    pass
            return True
    except Exception:
        return False

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

        # فقط کسر هزینه و اضافه کردن به کوله‌پشتی — اثر آیتم هنگام استفاده اعمال می‌شود
        await db.execute(
            "UPDATE users SET coins=coins-?, soul_gems=soul_gems-? WHERE user_id=?",
            (item["price_coins"], item["price_gems"], user_id)
        )
        qty = item["quantity"] if item["quantity"] else 1
        await db.execute(
            """INSERT INTO inventory(user_id, item_id, quantity)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id, item_id)
               DO UPDATE SET quantity = inventory.quantity + EXCLUDED.quantity""",
            (user_id, item_id, qty)
        )
        await db.commit()
        try:
            await _bump_mission(user_id, "shop", 1)
        except Exception:
            pass
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
                   ON CONFLICT(user_id,item_id) DO UPDATE SET quantity = inventory.quantity + EXCLUDED.quantity""",
                (user_id, reward["id"], reward["quantity"] or 1)
            )
            effect_text = f"🎁 جایزه تصادفی: {reward['name']} × {reward['quantity']}"
        else:
            changes = []
            if item["energy_gain"]:
                await db.execute("UPDATE users SET energy=energy+? WHERE user_id=?", (item["energy_gain"], user_id))
                changes.append(f"💠 +{item['energy_gain']} انرژی")
            health_g = 0
            try:
                health_g = int(item["health_gain"] or 0)
            except Exception:
                health_g = 0
            # آیتم‌های شفابخش شناخته‌شده
            if health_g <= 0 and any(x in item["name"] for x in ("شفا", "معجون", "باند", "دارو", "احیا")):
                health_g = 40 if "احیا" in item["name"] else 25
            if health_g > 0:
                cur2 = await db.execute(
                    "SELECT health, max_health FROM users WHERE user_id=?", (user_id,)
                )
                ur = await cur2.fetchone()
                max_hp = int(ur["max_health"] or 100) if ur else 100
                new_hp = min(max_hp, max(0, int(ur["health"] or 0)) + health_g)
                await db.execute(
                    "UPDATE users SET health=?, dead_until=NULL WHERE user_id=?",
                    (new_hp, user_id),
                )
                changes.append(f"❤️ +{health_g} سلامتی → {new_hp}/{max_hp}")
            if item["mission_bonus"]:
                await db.execute("UPDATE users SET spirit_power=spirit_power+? WHERE user_id=?", (item["mission_bonus"], user_id))
                changes.append(f"🔮 +{item['mission_bonus']} قدرت روح")
            try:
                hg = int(item["hunger_gain"] or 0)
            except Exception:
                hg = 0
            try:
                tg = int(item["thirst_gain"] or 0)
            except Exception:
                tg = 0
            if hg > 0 or tg > 0:
                await db.execute(
                    """UPDATE users SET
                       hunger=LEAST(100, COALESCE(hunger,100)+?),
                       thirst=LEAST(100, COALESCE(thirst,100)+?)
                       WHERE user_id=?""",
                    (hg, tg, user_id),
                )
                if hg:
                    changes.append(f"🍗 +{hg} سیری")
                if tg:
                    changes.append(f"💧 +{tg} سیرابی")
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
        cur = await db.execute(
            "SELECT clue_index, status, COALESCE(mistakes,0) FROM spirit_progress WHERE user_id=? AND spirit_id=?",
            (user_id, sid),
        )
        return await cur.fetchone()


async def get_next_clue(user_id,sid):
    progress = await get_spirit_progress(user_id, sid)
    idx = progress[0] if progress else 0
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM spirit_clues WHERE spirit_id=? ORDER BY clue_order LIMIT 1 OFFSET ?",
            (sid, idx),
        )
        return await cur.fetchone()


async def advance_spirit(user_id, sid, correct):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT clue_index, status, COALESCE(mistakes,0) FROM spirit_progress WHERE user_id=? AND spirit_id=?",
            (user_id, sid),
        )
        row = await cur.fetchone()
        idx = row[0] if row else 0
        mistakes = int(row[2]) if row else 0
        if not correct:
            mistakes += 1
            await db.execute(
                """INSERT INTO spirit_progress(user_id,spirit_id,clue_index,status,mistakes)
                   VALUES (?,?,?,?,?)
                   ON CONFLICT(user_id,spirit_id) DO UPDATE SET mistakes=EXCLUDED.mistakes""",
                (user_id, sid, idx, "active", mistakes),
            )
            await db.commit()
            return False, idx, False
        idx += 1
        cur = await db.execute("SELECT COUNT(*) FROM spirit_clues WHERE spirit_id=?", (sid,))
        total = (await cur.fetchone())[0]
        status = "completed" if idx >= total else "active"
        await db.execute(
            """INSERT INTO spirit_progress(user_id,spirit_id,clue_index,status,mistakes)
               VALUES (?,?,?,?,?)
               ON CONFLICT(user_id,spirit_id)
               DO UPDATE SET clue_index=EXCLUDED.clue_index, status=EXCLUDED.status, mistakes=EXCLUDED.mistakes""",
            (user_id, sid, idx, status, mistakes),
        )
        await db.commit()
        return True, idx, status == "completed"


def current_season_id() -> str:
    """فصل ماهانه: YYYY-MM به وقت تهران."""
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Asia/Tehran"))
    except Exception:
        now = datetime.now(timezone.utc)
    return f"{now.year:04d}-{now.month:02d}"


async def add_season_points(user_id: int, points: int):
    if points <= 0:
        return
    season = current_season_id()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO season_scores(user_id, season_id, points)
               VALUES (?,?,?)
               ON CONFLICT(user_id, season_id)
               DO UPDATE SET points = season_scores.points + EXCLUDED.points""",
            (user_id, season, points),
        )
        await db.commit()


async def top_season(limit: int = 10):
    season = current_season_id()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT u.name, u.level, s.points
               FROM season_scores s
               JOIN users u ON u.user_id = s.user_id
               WHERE s.season_id = ?
               ORDER BY s.points DESC, u.xp DESC
               LIMIT ?""",
            (season, limit),
        )
        return season, await cur.fetchall()

async def list_demons(region_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory=aiosqlite.Row
        if region_id: cur=await db.execute("SELECT d.*,r.name region_name FROM demons d JOIN regions r ON r.id=d.region_id WHERE d.active=1 AND d.region_id=? ORDER BY d.rank,d.id",(region_id,))
        else: cur=await db.execute("SELECT d.*,r.name region_name FROM demons d JOIN regions r ON r.id=d.region_id WHERE d.active=1 ORDER BY d.rank,d.id")
        return await cur.fetchall()

async def get_demon(did):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory=aiosqlite.Row; cur=await db.execute("SELECT d.*,r.name region_name FROM demons d JOIN regions r ON r.id=d.region_id WHERE d.id=? AND d.active=1",(did,)); return await cur.fetchone()

async def get_or_create_encounter(user_id, did):
    """برگرداندن یا ساخت encounter جن برای کاربر. همیشه Row (dict-like) برمی‌گرداند."""
    d = await get_demon(did)
    if not d:
        return None
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM demon_encounters WHERE user_id=? AND demon_id=?",
            (user_id, did)
        )
        row = await cur.fetchone()
        if not row:
            await db.execute(
                "INSERT INTO demon_encounters(user_id,demon_id,health,corruption,stage,status) VALUES (?,?,?,?,1,'active')",
                (user_id, did, d["health"], d["corruption"])
            )
            await db.commit()
            cur = await db.execute(
                "SELECT * FROM demon_encounters WHERE user_id=? AND demon_id=?",
                (user_id, did)
            )
            row = await cur.fetchone()
        return row

async def update_encounter(user_id, did, health, corruption, stage, status="active"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE demon_encounters SET health=?, corruption=?, stage=?, status=? WHERE user_id=? AND demon_id=?",
            (health, corruption, stage, status, user_id, did)
        )
        await db.commit()

async def reset_encounter(user_id, did):
    """اجازه مبارزه دوباره با جن بعد از پاک‌سازی (با هزینه کمی سکه/انرژی در لایه بازی)."""
    d = await get_demon(did)
    if not d:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE demon_encounters SET health=?, corruption=?, stage=1, status='active' WHERE user_id=? AND demon_id=?",
            (d["health"], d["corruption"], user_id, did)
        )
        await db.commit()
    return True

# ─── سختی بازی (تقریباً ۳۰× سخت‌تر از نسخهٔ اولیه) ───
# هزینه انرژی
ENERGY_CLUE = 4          # هر انتخاب سرنخ
ENERGY_SEAL = 8          # مهر محافظ
ENERGY_CLEAN = 10        # پاک‌سازی
ENERGY_RESET = 25        # مبارزه دوباره با جن
ENERGY_TRAIN = 5         # پرورش ذهن
# محدودیت روزانه مأموریت
DAILY_SPIRIT_LIMIT = 3
DAILY_CLEANSE_LIMIT = 2
# آسیب سلامتی
DAMAGE_WRONG_CLUE = 18
DAMAGE_DEMON_HIT_MIN = 12
DAMAGE_DEMON_HIT_MAX = 35
# مرگ
DEATH_COOLDOWN_MINUTES = 45
DEATH_COIN_LOSS_PCT = 35


async def spend_energy(user_id: int, amount: int) -> bool:
    """کم کردن انرژی؛ اگر کافی نباشد یا بازیکن مرده باشد False."""
    if await is_dead(user_id):
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT energy FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if not row or row["energy"] < amount:
            return False
        await db.execute("UPDATE users SET energy=energy-? WHERE user_id=?", (amount, user_id))
        await db.commit()
        return True


async def is_dead(user_id: int) -> bool:
    """اگر بازیکن در حالت مرگ باشد True."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT health, dead_until FROM users WHERE user_id=?", (user_id,)
            )
            row = await cur.fetchone()
            if not row:
                return False
            if row["health"] is not None and int(row["health"]) <= 0:
                return True
            until = row["dead_until"] if "dead_until" in row.keys() else None
            if until:
                try:
                    if datetime.fromisoformat(str(until)) > datetime.now(timezone.utc):
                        return True
                    # زمان مرگ تمام شده — احیای ضعیف
                    await db.execute(
                        "UPDATE users SET health=GREATEST(health, 15), dead_until=NULL WHERE user_id=?",
                        (user_id,),
                    )
                    await db.commit()
                except Exception:
                    pass
            return False
    except Exception:
        return False


async def apply_damage(user_id: int, amount: int) -> tuple:
    """اعمال آسیب. برمی‌گرداند (alive: bool, health: int, died: bool, msg: str)."""
    amount = max(0, int(amount))
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT health, max_health, coins, deaths FROM users WHERE user_id=?",
            (user_id,),
        )
        row = await cur.fetchone()
        if not row:
            return False, 0, False, "کاربر پیدا نشد."
        hp = max(0, int(row["health"] or 0) - amount)
        max_hp = int(row["max_health"] or 100)
        if hp > 0:
            await db.execute(
                "UPDATE users SET health=? WHERE user_id=?", (hp, user_id)
            )
            await db.commit()
            return True, hp, False, f"❤️ -{amount} سلامتی (باقی‌مانده: {hp}/{max_hp})"

        # مرگ
        from datetime import timedelta
        until = (datetime.now(timezone.utc) + timedelta(minutes=DEATH_COOLDOWN_MINUTES)).isoformat()
        coins = int(row["coins"] or 0)
        lost = int(coins * DEATH_COIN_LOSS_PCT / 100)
        deaths = int(row["deaths"] or 0) + 1
        await db.execute(
            """UPDATE users SET health=0, energy=0, coins=coins-?, deaths=?, dead_until=?
               WHERE user_id=?""",
            (lost, deaths, until, user_id),
        )
        await db.commit()
        msg = (
            f"💀 <b>مرگ روحی!</b>\n\n"
            f"سلامتی‌ات به صفر رسید.\n"
            f"🪙 -{lost} سکه ({DEATH_COIN_LOSS_PCT}٪)\n"
            f"💠 انرژی صفر شد\n"
            f"⏳ تا {DEATH_COOLDOWN_MINUTES} دقیقه نمی‌توانی مأموریت بروی.\n\n"
            f"برای زودتر برگشتن: آیتم شفا از فروشگاه یا /revive با کریستال."
        )
        return False, 0, True, msg


async def heal_user(user_id: int, amount: int) -> tuple:
    """شفا. برمی‌گرداند (ok, new_health, msg)."""
    amount = max(0, int(amount))
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT health, max_health, dead_until FROM users WHERE user_id=?",
            (user_id,),
        )
        row = await cur.fetchone()
        if not row:
            return False, 0, "کاربر پیدا نشد."
        max_hp = int(row["max_health"] or 100)
        hp = min(max_hp, max(0, int(row["health"] or 0)) + amount)
        await db.execute(
            "UPDATE users SET health=?, dead_until=NULL WHERE user_id=?",
            (hp, user_id),
        )
        await db.commit()
        return True, hp, f"❤️ +{amount} سلامتی → {hp}/{max_hp}"


async def revive_with_gems(user_id: int, cost: int = 5) -> tuple:
    """احیا با کریستال."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT soul_gems, max_health, health, dead_until FROM users WHERE user_id=?",
            (user_id,),
        )
        row = await cur.fetchone()
        if not row:
            return False, "کاربر پیدا نشد."
        if int(row["health"] or 0) > 0 and not row["dead_until"]:
            return False, "نیازی به احیا نداری؛ زنده هستی."
        if int(row["soul_gems"] or 0) < cost:
            return False, f"حداقل {cost} کریستال لازم است."
        max_hp = int(row["max_health"] or 100)
        half = max(25, max_hp // 2)
        await db.execute(
            """UPDATE users SET soul_gems=soul_gems-?, health=?, energy=energy+3, dead_until=NULL
               WHERE user_id=?""",
            (cost, half, user_id),
        )
        await db.commit()
        return True, f"✨ احیا شدی!\n❤️ سلامتی: {half}/{max_hp}\n💠 +3 انرژی\n🔮 -{cost} کریستال"


async def check_mission_limit(user_id: int, kind: str) -> tuple:
    """kind: spirit | cleanse — آیا هنوز سهمیه روزانه دارد؟"""
    day = _today_tehran()
    limit = DAILY_SPIRIT_LIMIT if kind == "spirit" else DAILY_CLEANSE_LIMIT
    key = f"limit_{kind}"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT progress FROM user_missions WHERE user_id=? AND mission_key=? AND day=?",
            (user_id, key, day),
        )
        row = await cur.fetchone()
        used = int(row["progress"]) if row else 0
        if used >= limit:
            label = "روح" if kind == "spirit" else "پاک‌سازی جن"
            return False, f"⛔ سهمیه روزانه {label} تمام شده ({limit}/{limit}). فردا دوباره بیا."
        return True, f"{used}/{limit}"


async def bump_mission_limit(user_id: int, kind: str):
    key = f"limit_{kind}"
    day = _today_tehran()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO user_missions(user_id, mission_key, day, progress, claimed)
               VALUES (?, ?, ?, 1, 0)
               ON CONFLICT(user_id, mission_key, day)
               DO UPDATE SET progress = user_missions.progress + 1""",
            (user_id, key, day),
        )
        await db.commit()


async def require_alive(user_id: int) -> tuple:
    """قبل از مأموریت: (ok, error_message)."""
    if await is_dead(user_id):
        return False, (
            "💀 تو در حالت مرگ روحی هستی.\n"
            f"صبر کن یا با /revive ({5} کریستال) یا آیتم شفا از فروشگاه برگرد."
        )
    return True, ""

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
        await db.execute("UPDATE children SET happiness=LEAST(100,happiness+10), health=LEAST(100,health+5) WHERE id=?", (child_id,))
        await db.commit()
    return True


async def train_mind(user_id: int):
    """پرورش ذهن؛ هر ۱۵ دقیقه یک بار — نسخه سخت."""
    from datetime import datetime, timezone, timedelta
    if await is_dead(user_id):
        return False, "💀 در حالت مرگ نمی‌توانی تمرین کنی. /revive"
    now = datetime.now(timezone.utc)
    cooldown = timedelta(minutes=15)
    cost = ENERGY_TRAIN
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT energy, mind_power, training_points, last_training FROM users WHERE user_id=?",
            (user_id,),
        )
        u = await cur.fetchone()
        if not u:
            return False, "کاربر پیدا نشد."
        last = u["last_training"]
        if last:
            try:
                if "T" in str(last) or " " in str(last):
                    last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
                    if last_dt.tzinfo is None:
                        last_dt = last_dt.replace(tzinfo=timezone.utc)
                else:
                    last_dt = None
                if last_dt is not None:
                    remaining = (last_dt + cooldown) - now
                    if remaining.total_seconds() > 0:
                        mins = int(remaining.total_seconds() // 60) + 1
                        return False, f"هنوز {mins} دقیقه تا تمرین بعدی باقی مانده."
            except Exception:
                pass
        if u["energy"] < cost:
            return False, f"برای تمرین ذهن حداقل {cost} انرژی لازم داری."
        gain = 1 + (u["training_points"] // 15)
        stamp = now.isoformat()
        await db.execute(
            "UPDATE users SET energy=energy-?, mind_power=mind_power+?, training_points=training_points+1, xp=xp+?, last_training=? WHERE user_id=?",
            (cost, gain, 3 + gain, stamp, user_id),
        )
        await db.commit()
        try:
            await _bump_mission(user_id, "train", 1)
        except Exception:
            pass
        return True, gain

async def get_training_stats(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT mind_power, body_power, spirit_power, training_points FROM users WHERE user_id=?", (user_id,))
        return await cur.fetchone()
