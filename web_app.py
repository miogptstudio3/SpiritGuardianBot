"""
Spirit Guardian — Advanced Telegram Web App backend
"""
import os
import json
import hmac
import hashlib
import urllib.parse
from datetime import datetime, timezone, timedelta

from aiohttp import web
import aiosqlite

DB_PATH = os.getenv("DATABASE_URL", "").strip()
if not DB_PATH:
    raise RuntimeError("DATABASE_URL در فایل .env تنظیم نشده است.")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_db_dir = os.path.dirname(DB_PATH)
if _db_dir:
    os.makedirs(_db_dir, exist_ok=True)


# ─── Auth ───────────────────────────────────────────────────────────
def validate_init_data(init_data: str):
    if not init_data or not BOT_TOKEN:
        return None
    try:
        data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        received = data.pop("hash", None)
        if not received:
            return None
        auth_date = int(data.get("auth_date", "0"))
        if abs(datetime.now(timezone.utc).timestamp() - auth_date) > 86400:
            return None
        check_string = "\n".join(f"{k}={data[k]}" for k in sorted(data))
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, received):
            return None
        user = json.loads(data.get("user", "{}"))
        return user if user.get("id") else None
    except Exception:
        return None


# ─── DB helpers ─────────────────────────────────────────────────────
async def db_one(sql, args=()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(sql, args)
        return await cur.fetchone()


async def db_all(sql, args=()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(sql, args)
        return await cur.fetchall()


async def db_exec(sql, args=()):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(sql, args)
        await db.commit()


async def current_user(request):
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    # Also accept query param for some Telegram clients
    if not init_data:
        init_data = request.rel_url.query.get("initData", "")
    user = validate_init_data(init_data)
    if not user:
        raise web.HTTPUnauthorized(text="ابتدا Web App را از داخل ربات تلگرام باز کن.")
    row = await db_one("SELECT * FROM users WHERE user_id=?", (user["id"],))
    if not row:
        name = user.get("first_name") or user.get("username") or "بازیکن"
        await db_exec(
            "INSERT INTO users(user_id,name) VALUES(?,?) ON CONFLICT(user_id) DO NOTHING",
            (user["id"], name[:80]),
        )
        row = await db_one("SELECT * FROM users WHERE user_id=?", (user["id"],))
    return row


def row_to_user(u):
    """Normalize user row for frontend (map DB names → friendly keys)."""
    d = dict(u)
    boost = int(d.get("coin_boost") or 0)
    return {
        "user_id": d["user_id"],
        "name": d.get("name") or "بازیکن",
        "level": d.get("level") or 1,
        "xp": d.get("xp") or 0,
        "coins": d.get("coins") or 0,
        "energy": d.get("energy") or 0,
        "health": d.get("health") or 100,
        "max_health": d.get("max_health") or 100,
        "soul_gems": d.get("soul_gems") or 0,
        "light": d.get("light") or 0,
        "spirits_sent": d.get("spirits_sent") or 0,
        "cleanses": d.get("cleanses") or 0,
        "mind_power": d.get("mind_power") or 1,
        "body_power": d.get("body_power") or 1,
        "spirit_power": d.get("spirit_power") or 1,
        "training_points": d.get("training_points") or 0,
        "coin_boost": boost,
        "coin_bonus_pct": min(boost * 5, 50),
        "gender": d.get("gender"),
        "last_daily": d.get("last_daily"),
        "last_training": d.get("last_training"),
    }


# ─── Routes ─────────────────────────────────────────────────────────
async def health(request):
    return web.json_response(
        {"ok": True, "service": "spirit-guardian-web", "version": "2.3",
         "time": datetime.now(timezone.utc).isoformat()}
    )


async def me(request):
    u = await current_user(request)
    return web.json_response(row_to_user(u))


async def inventory(request):
    u = await current_user(request)
    rows = await db_all(
        """SELECT i.item_id, i.quantity, s.name, s.description, s.category,
                  s.energy_gain, s.mission_bonus
           FROM inventory i JOIN shop_items s ON s.id=i.item_id
           WHERE i.user_id=? AND i.quantity>0 AND s.active=1
           ORDER BY i.quantity DESC, i.item_id""",
        (u["user_id"],),
    )
    return web.json_response([dict(r) for r in rows])


async def use_item(request):
    u = await current_user(request)
    try:
        item_id = int(request.match_info["item_id"])
    except ValueError:
        raise web.HTTPBadRequest(text="آیتم نامعتبر")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT i.quantity, s.name, s.energy_gain, s.mission_bonus, s.category
               FROM inventory i JOIN shop_items s ON s.id=i.item_id
               WHERE i.user_id=? AND i.item_id=? AND i.quantity>0 AND s.active=1""",
            (u["user_id"], item_id),
        )
        item = await cur.fetchone()
        if not item:
            raise web.HTTPNotFound(text="آیتم پیدا نشد")
        await db.execute(
            "UPDATE inventory SET quantity=quantity-1 WHERE user_id=? AND item_id=? AND quantity>0",
            (u["user_id"], item_id),
        )
        await db.execute(
            """UPDATE users SET energy=LEAST(100, energy+?),
               spirit_power=spirit_power+?, xp=xp+? WHERE user_id=?""",
            (
                item["energy_gain"],
                item["mission_bonus"],
                max(1, item["mission_bonus"] // 2),
                u["user_id"],
            ),
        )
        await db.commit()
    return web.json_response({"ok": True, "message": f"{item['name']} استفاده شد."})


async def shop(request):
    rows = await db_all(
        """SELECT id, name, description, category, price_coins, price_gems,
                  energy_gain, mission_bonus
           FROM shop_items WHERE active=1 ORDER BY category, id"""
    )
    return web.json_response([dict(r) for r in rows])


async def buy(request):
    u = await current_user(request)
    item_id = int(request.match_info["item_id"])
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        item = await (
            await db.execute(
                "SELECT * FROM shop_items WHERE id=? AND active=1", (item_id,)
            )
        ).fetchone()
        if not item:
            raise web.HTTPNotFound(text="آیتم پیدا نشد")
        if u["coins"] < item["price_coins"] or u["soul_gems"] < item["price_gems"]:
            raise web.HTTPBadRequest(text="سکه یا کریستال کافی نیست")
        await db.execute(
            "UPDATE users SET coins=coins-?, soul_gems=soul_gems-? WHERE user_id=?",
            (item["price_coins"], item["price_gems"], u["user_id"]),
        )
        await db.execute(
            """INSERT INTO inventory(user_id,item_id,quantity) VALUES(?,?,?)
               ON CONFLICT(user_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity""",
            (u["user_id"], item_id, item["quantity"] or 1),
        )
        await db.commit()
    return web.json_response({"ok": True, "message": "خرید با موفقیت انجام شد 🛒"})


async def train(request):
    u = await current_user(request)
    now = datetime.now(timezone.utc)
    cooldown = timedelta(minutes=5)
    last = u["last_training"]
    if last:
        try:
            last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            remaining = (last_dt + cooldown) - now
            if remaining.total_seconds() > 0:
                mins = int(remaining.total_seconds() // 60) + 1
                raise web.HTTPBadRequest(
                    text=f"هنوز {mins} دقیقه تا تمرین بعدی باقی مانده."
                )
        except web.HTTPBadRequest:
            raise
        except Exception:
            pass
    if (u["energy"] or 0) < 1:
        raise web.HTTPBadRequest(text="انرژی کافی نداری.")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE users SET mind_power=mind_power+1, training_points=training_points+1,
               xp=xp+25, energy=energy-1, last_training=? WHERE user_id=?""",
            (now.isoformat(), u["user_id"]),
        )
        await db.commit()
    return web.json_response(
        {
            "ok": True,
            "message": "🧠 پرورش ذهن انجام شد! قدرت ذهن +۱ و XP +۲۵ — تمرین بعدی بعد از ۵ دقیقه",
        }
    )


async def stories(request):
    rows = await db_all(
        """SELECT s.id, s.name, s.age, s.type, s.difficulty, s.status, s.request,
                  s.story, s.reward_coins, s.reward_xp, r.name region_name
           FROM spirits_story s JOIN regions r ON r.id=s.region_id
           WHERE s.active=1 ORDER BY s.difficulty, s.id"""
    )
    return web.json_response([dict(r) for r in rows])


async def demons_api(request):
    u = await current_user(request)
    rows = await db_all(
        """SELECT d.id, d.name, d.type, d.rank, d.health, d.corruption, d.defense,
                  d.story, d.reward_coins, d.reward_xp, r.name region_name
           FROM demons d JOIN regions r ON r.id=d.region_id
           WHERE d.active=1 ORDER BY d.rank, d.id"""
    )
    result = []
    for d in rows:
        e = await db_one(
            "SELECT health, corruption, stage, status FROM demon_encounters WHERE user_id=? AND demon_id=?",
            (u["user_id"], d["id"]),
        )
        item = dict(d)
        if e:
            item["encounter_health"] = e["health"]
            item["encounter_corruption"] = e["corruption"]
            item["encounter_status"] = e["status"]
            item["stage"] = e["stage"]
        else:
            item["encounter_health"] = d["health"]
            item["encounter_corruption"] = d["corruption"]
            item["encounter_status"] = "none"
            item["stage"] = 0
        result.append(item)
    return web.json_response(result)


async def regions_api(request):
    u = await current_user(request)
    rows = await db_all(
        "SELECT id, name, description, unlock_level FROM regions WHERE active=1 ORDER BY unlock_level, id"
    )
    level = u["level"] or 1
    out = []
    for r in rows:
        item = dict(r)
        item["unlocked"] = level >= r["unlock_level"]
        out.append(item)
    return web.json_response(out)


async def rank_api(request):
    await current_user(request)
    rows = await db_all(
        """SELECT name, level, spirits_sent, cleanses, xp
           FROM users ORDER BY spirits_sent + cleanses DESC, xp DESC LIMIT 15"""
    )
    return web.json_response([dict(r) for r in rows])


async def daily_api(request):
    u = await current_user(request)
    try:
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("Asia/Tehran")).date().isoformat()
    except Exception:
        today = datetime.now(timezone.utc).date().isoformat()
    if u["last_daily"] == today:
        raise web.HTTPBadRequest(text="پاداش امروز را قبلاً گرفته‌ای. فردا دوباره بیا.")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET coins=coins+100, energy=LEAST(100, energy+5), last_daily=? WHERE user_id=?",
            (today, u["user_id"]),
        )
        await db.commit()
    return web.json_response(
        {"ok": True, "message": "🎁 پاداش روزانه دریافت شد!\n🪙 +100 سکه\n💠 +5 انرژی"}
    )


async def upgrade_coins_api(request):
    u = await current_user(request)
    level = int(u["coin_boost"] or 0) if "coin_boost" in u.keys() else 0
    if level >= 10:
        raise web.HTTPBadRequest(text="ارتقای سکه به حداکثر سطح (۱۰) رسیده است.")
    cost_coins = int(500 * (1.6 ** level))
    cost_gems = 2 + level
    if u["coins"] < cost_coins or u["soul_gems"] < cost_gems:
        raise web.HTTPBadRequest(
            text=f"منابع کافی نیست.\nنیاز: 🪙 {cost_coins} + 🔮 {cost_gems}\nموجودی: 🪙 {u['coins']} | 🔮 {u['soul_gems']}"
        )
    new_level = level + 1
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET coins=coins-?, soul_gems=soul_gems-?, coin_boost=? WHERE user_id=?",
            (cost_coins, cost_gems, new_level, u["user_id"]),
        )
        await db.commit()
    bonus = min(new_level * 5, 50)
    return web.json_response(
        {
            "ok": True,
            "message": f"✅ کیف پول ارتقا یافت!\nسطح: {new_level}/10\nپاداش سکه: +{bonus}٪",
            "level": new_level,
            "bonus_pct": bonus,
        }
    )


async def family_api(request):
    u = await current_user(request)
    rows = await db_all(
        """SELECT m.*, u1.name name1, u2.name name2
           FROM marriages m
           JOIN users u1 ON u1.user_id=m.user1_id
           JOIN users u2 ON u2.user_id=m.user2_id
           WHERE m.user1_id=? OR m.user2_id=?
           ORDER BY m.id DESC""",
        (u["user_id"], u["user_id"]),
    )
    kids = await db_all(
        "SELECT * FROM children WHERE parent1_id=? OR parent2_id=? ORDER BY id DESC",
        (u["user_id"], u["user_id"]),
    )
    return web.json_response(
        {"marriages": [dict(x) for x in rows], "children": [dict(x) for x in kids]}
    )


async def index(request):
    return web.FileResponse(os.path.join(BASE_DIR, "index.html"))


# CORS middleware for safety
@web.middleware
async def cors_middleware(request, handler):
    if request.method == "OPTIONS":
        resp = web.Response(status=204)
    else:
        try:
            resp = await handler(request)
        except web.HTTPException as e:
            resp = e
            # convert to JSON body when possible
            if not isinstance(resp, web.Response):
                resp = web.Response(text=str(e.text or e.reason), status=e.status)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "X-Telegram-Init-Data, Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


app = web.Application(middlewares=[cors_middleware])
app.add_routes(
    [
        web.get("/", index),
        web.get("/health", health),
        web.get("/api/me", me),
        web.get("/api/inventory", inventory),
        web.post("/api/inventory/{item_id}/use", use_item),
        web.get("/api/shop", shop),
        web.post("/api/shop/{item_id}/buy", buy),
        web.post("/api/train/mind", train),
        web.get("/api/stories", stories),
        web.get("/api/demons", demons_api),
        web.get("/api/regions", regions_api),
        web.get("/api/rank", rank_api),
        web.post("/api/daily", daily_api),
        web.post("/api/upgrade_coins", upgrade_coins_api),
        web.get("/api/family", family_api),
        web.static("/static", os.path.join(BASE_DIR, "static")),
    ]
)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    web.run_app(app, host="0.0.0.0", port=port)
