import os, json, hmac, hashlib, urllib.parse, secrets
from datetime import datetime, timezone, date
from aiohttp import web
import aiosqlite

DB_PATH = os.getenv('DB_PATH', '/var/data/spirits.db' if os.path.isdir('/var/data') else 'spirits.db')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Ensure parent directory of DB exists (critical for /var/data persistent disk)
_db_dir = os.path.dirname(DB_PATH)
if _db_dir:
    os.makedirs(_db_dir, exist_ok=True)


def validate_init_data(init_data: str):
    if not init_data or not BOT_TOKEN:
        return None
    try:
        data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        received = data.pop('hash', None)
        if not received:
            return None
        auth_date = int(data.get('auth_date', '0'))
        if abs(datetime.now(timezone.utc).timestamp() - auth_date) > 86400:
            return None
        check_string = '\n'.join(f'{k}={data[k]}' for k in sorted(data))
        secret = hmac.new(b'WebAppData', BOT_TOKEN.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, received):
            return None
        user = json.loads(data.get('user', '{}'))
        return user if user.get('id') else None
    except Exception:
        return None


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


async def current_user(request):
    init_data = request.headers.get('X-Telegram-Init-Data', '')
    user = validate_init_data(init_data)
    if not user:
        raise web.HTTPUnauthorized(text='Telegram Web App authentication required')
    row = await db_one('SELECT * FROM users WHERE user_id=?', (user['id'],))
    if not row:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('INSERT INTO users(user_id,name) VALUES(?,?)', (user['id'], user.get('first_name','بازیکن')))
            await db.commit()
        row = await db_one('SELECT * FROM users WHERE user_id=?', (user['id'],))
    return row


async def health(request):
    return web.json_response({'ok': True, 'service': 'spirit-guardian-web', 'time': datetime.now(timezone.utc).isoformat()})


async def me(request):
    u = await current_user(request)
    return web.json_response(dict(u))


async def inventory(request):
    u = await current_user(request)
    rows = await db_all('''SELECT i.item_id, i.quantity, s.name, s.description, s.category, s.energy_gain, s.mission_bonus
                           FROM inventory i JOIN shop_items s ON s.id=i.item_id
                           WHERE i.user_id=? AND i.quantity>0 AND s.active=1 ORDER BY i.quantity DESC, i.item_id''', (u['user_id'],))
    return web.json_response([dict(r) for r in rows])


async def use_item(request):
    u = await current_user(request)
    try: item_id = int(request.match_info['item_id'])
    except ValueError: raise web.HTTPBadRequest(text='invalid item')
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute('''SELECT i.quantity,s.name,s.energy_gain,s.mission_bonus,s.category FROM inventory i JOIN shop_items s ON s.id=i.item_id WHERE i.user_id=? AND i.item_id=? AND i.quantity>0 AND s.active=1''', (u['user_id'],item_id))
        item = await cur.fetchone()
        if not item: raise web.HTTPNotFound(text='item not found')
        await db.execute('UPDATE inventory SET quantity=quantity-1 WHERE user_id=? AND item_id=? AND quantity>0', (u['user_id'],item_id))
        await db.execute('''UPDATE users SET energy=MIN(100, energy+?), spirit_power=spirit_power+?, xp=xp+? WHERE user_id=?''', (item['energy_gain'], item['mission_bonus'], max(1,item['mission_bonus']//2),u['user_id']))
        await db.commit()
    return web.json_response({'ok':True,'message':f"{item['name']} استفاده شد."})


async def shop(request):
    rows = await db_all('SELECT id,name,description,category,price_coins,price_gems,energy_gain,mission_bonus FROM shop_items WHERE active=1 ORDER BY category,id')
    return web.json_response([dict(r) for r in rows])


async def buy(request):
    u = await current_user(request)
    item_id = int(request.match_info['item_id'])
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        item = await (await db.execute('SELECT * FROM shop_items WHERE id=? AND active=1',(item_id,))).fetchone()
        if not item: raise web.HTTPNotFound(text='item not found')
        if u['coins'] < item['price_coins'] or u['soul_gems'] < item['price_gems']:
            raise web.HTTPBadRequest(text='منابع کافی نیست')
        await db.execute('UPDATE users SET coins=coins-?, soul_gems=soul_gems-? WHERE user_id=?', (item['price_coins'],item['price_gems'],u['user_id']))
        await db.execute('''INSERT INTO inventory(user_id,item_id,quantity) VALUES(?,?,?) ON CONFLICT(user_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity''', (u['user_id'],item_id,item['quantity']))
        await db.commit()
    return web.json_response({'ok':True,'message':'خرید با موفقیت انجام شد'})


async def train(request):
    u = await current_user(request)
    # همان منطق ۵ دقیقه‌ای ربات
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    cooldown = timedelta(minutes=5)
    last = u['last_training']
    if last:
        try:
            if 'T' in str(last) or ' ' in str(last):
                last_dt = datetime.fromisoformat(str(last).replace('Z', '+00:00'))
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                remaining = (last_dt + cooldown) - now
                if remaining.total_seconds() > 0:
                    mins = int(remaining.total_seconds() // 60) + 1
                    raise web.HTTPBadRequest(text=f'هنوز {mins} دقیقه تا تمرین بعدی باقی مانده.')
        except web.HTTPBadRequest:
            raise
        except Exception:
            pass
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE users SET mind_power=mind_power+1, training_points=training_points+1, xp=xp+25, last_training=? WHERE user_id=?',
            (now.isoformat(), u['user_id'])
        )
        await db.commit()
    return web.json_response({'ok': True, 'message': 'پرورش ذهن انجام شد؛ قدرت ذهن +۱ و XP +۲۵ — تمرین بعدی بعد از ۵ دقیقه'})


async def stories(request):
    rows = await db_all('''SELECT s.id,s.name,s.age,s.type,s.difficulty,s.status,s.request,s.story,s.reward_coins,s.reward_xp,r.name region_name
                           FROM spirits_story s JOIN regions r ON r.id=s.region_id WHERE s.active=1 ORDER BY s.difficulty DESC,s.id''')
    return web.json_response([dict(r) for r in rows])


async def marriages(request):
    u = await current_user(request)
    rows = await db_all('''SELECT m.*, u1.name name1, u2.name name2 FROM marriages m JOIN users u1 ON u1.user_id=m.user1_id JOIN users u2 ON u2.user_id=m.user2_id WHERE m.user1_id=? OR m.user2_id=? ORDER BY m.id DESC''',(u['user_id'],u['user_id']))
    kids = await db_all('SELECT * FROM children WHERE parent1_id=? OR parent2_id=? ORDER BY id DESC',(u['user_id'],u['user_id']))
    return web.json_response({'marriages':[dict(x) for x in rows],'children':[dict(x) for x in kids]})


async def index(request):
    return web.FileResponse(os.path.join(BASE_DIR,'index.html'))

app = web.Application()
app.add_routes([
    web.get('/', index), web.get('/health', health), web.get('/api/me', me),
    web.get('/api/inventory', inventory), web.post('/api/inventory/{item_id}/use', use_item),
    web.get('/api/shop', shop), web.post('/api/shop/{item_id}/buy', buy),
    web.post('/api/train/mind', train), web.get('/api/stories', stories), web.get('/api/family', marriages),
    web.static('/static', os.path.join(BASE_DIR,'static')),
])

if __name__ == '__main__':
    port = int(os.getenv('PORT','10000'))
    web.run_app(app, host='0.0.0.0', port=port)
