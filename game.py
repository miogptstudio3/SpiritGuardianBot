import random
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import (
    ensure_user, get_user, top_users, daily_claim, list_shop_items, get_shop_item,
    buy_shop_item, get_inventory, use_inventory_item, list_regions, get_region,
    list_story_spirits, get_story_spirit, get_next_clue, advance_spirit,
    list_demons, get_demon, get_or_create_encounter, update_encounter, reset_encounter,
    add_progress, spend_energy, upgrade_coin_boost, create_marriage_proposal,
    get_pending_proposal, respond_marriage, get_marriage, list_children,
    adopt_child, care_for_child, train_mind, get_training_stats, DB_PATH,
    get_daily_missions, claim_mission_reward, top_season,
    require_alive, apply_damage, heal_user, revive_with_gems,
    check_mission_limit, bump_mission_limit, is_dead,
    apply_activity_needs, tick_needs,
    ENERGY_CLUE, ENERGY_SEAL, ENERGY_CLEAN, ENERGY_RESET,
    DAMAGE_WRONG_CLUE, DAMAGE_DEMON_HIT_MIN, DAMAGE_DEMON_HIT_MAX,
    DAILY_SPIRIT_LIMIT, DAILY_CLEANSE_LIMIT,
)
import aiosqlite

router=Router()

def main_game_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='👻 دفتر ارواح',callback_data='world:spirits'),InlineKeyboardButton(text='😈 جن‌ها',callback_data='world:demons')],
        [InlineKeyboardButton(text='🗺️ جهان',callback_data='world:regions'),InlineKeyboardButton(text='🎒 کوله‌پشتی',callback_data='world:inventory')],
        [InlineKeyboardButton(text='💍 خانواده',callback_data='world:family'),InlineKeyboardButton(text='🧠 پرورش ذهن',callback_data='training:mind')],
        [InlineKeyboardButton(text='📜 مأموریت کریستال',callback_data='missions:list')],
    ])


async def _safe_user(user_id: int, name: str = "بازیکن"):
    """اطمینان از وجود کاربر و برگرداندن ردیف؛ در صورت خطا None."""
    try:
        await ensure_user(user_id, name or "بازیکن")
        return await get_user(user_id)
    except Exception:
        return None


@router.message(Command('mind'))
@router.message(F.text=='🧠 پرورش ذهن')
@router.message(F.text=='پرورش ذهن')
async def mind_training(message:Message):
    u = await _safe_user(message.from_user.id, message.from_user.full_name)
    if not u:
        return await message.reply('⚠️ خطا در دریافت اطلاعات کاربر. دوباره /start بزن.')
    ok, result = await train_mind(message.from_user.id)
    if not ok:
        return await message.reply(f'🧠 {result}')
    u = await get_user(message.from_user.id)
    await message.reply(
        f'🧠 <b>تمرین ذهن با موفقیت انجام شد!</b>\n\n'
        f'✨ قدرت ذهن: +{result}\n'
        f'🏅 امتیاز تمرین: {u["training_points"]}\n'
        f'✨ XP: +{5 + result}\n'
        f'💠 انرژی باقی‌مانده: {u["energy"]}\n\n'
        f'⏳ تمرین بعدی بعد از ۵ دقیقه در دسترس است.'
    )


@router.callback_query(F.data=='training:mind')
async def mind_training_cb(call:CallbackQuery):
    # مهم: از call.from_user استفاده شود، نه call.message.from_user (که ربات است)
    u = await _safe_user(call.from_user.id, call.from_user.full_name)
    if not u:
        return await call.answer('⚠️ ابتدا /start را بزن.', show_alert=True)
    ok, result = await train_mind(call.from_user.id)
    if not ok:
        await call.answer(f'🧠 {result}', show_alert=True)
        return
    u = await get_user(call.from_user.id)
    await call.message.answer(
        f'🧠 <b>تمرین ذهن با موفقیت انجام شد!</b>\n\n'
        f'✨ قدرت ذهن: +{result}\n'
        f'🏅 امتیاز تمرین: {u["training_points"]}\n'
        f'✨ XP: +{5 + result}\n'
        f'💠 انرژی باقی‌مانده: {u["energy"]}\n\n'
        f'⏳ تمرین بعدی بعد از ۵ دقیقه در دسترس است.'
    )
    await call.answer()


@router.message(Command('stats'))
async def training_stats(message:Message):
    u = await _safe_user(message.from_user.id, message.from_user.full_name)
    if not u:
        return await message.reply('⚠️ خطا در دریافت اطلاعات. دوباره /start بزن.')
    await message.reply(
        f'📈 <b>آمار رشد شخصیت</b>\n\n'
        f'🧠 قدرت ذهن: {u["mind_power"]}\n'
        f'💪 قدرت جسم: {u["body_power"]}\n'
        f'🔮 قدرت روح: {u["spirit_power"]}\n'
        f'🏅 امتیاز تمرین: {u["training_points"]}\n'
        f'⭐ سطح: {u["level"]}'
    )


@router.message(Command('profile'))
@router.message(F.text == '👤 پروفایل')
async def profile(message: Message):
    u = await _safe_user(message.from_user.id, message.from_user.full_name)
    if not u:
        return await message.reply('⚠️ خطا در دریافت پروفایل. دوباره /start بزن.')
    boost = int(u['coin_boost'] or 0) if 'coin_boost' in u.keys() else 0
    bonus = min(boost * 5, 50)
    deaths = u['deaths'] if 'deaths' in u.keys() else 0
    dead = await is_dead(message.from_user.id)
    status = '💀 مرگ روحی' if dead else '✅ زنده'
    await message.reply(
        f'''👤 <b>پروفایل راهنمای ارواح</b>

نام: {u['name']}
وضعیت: {status}
⭐ سطح راهنمایی: {u['level']}
✨ تجربه: {u['xp']}
❤️ سلامتی: {u['health']}/{u['max_health']}
💠 انرژی روحی: {u['energy']}
🪙 سکه: {u['coins']}
🔮 کریستال سایه: {u['soul_gems']}
✨ نور پسین: {u['light'] if 'light' in u.keys() else 0}
🍗 گرسنگی: {u['hunger'] if 'hunger' in u.keys() else 100}/100
💧 تشنگی: {u['thirst'] if 'thirst' in u.keys() else 100}/100
💰 ارتقای سکه: سطح {boost}/10 (+{bonus}٪ پاداش)
👻 ارواح راهی‌شده: {u['spirits_sent']}
😈 پاک‌سازی‌ها: {u['cleanses']}
💀 مرگ‌ها: {deaths}
🧠 قدرت ذهن: {u['mind_power']}
💪 قدرت جسم: {u['body_power']}
🔮 قدرت روح: {u['spirit_power']}
🏅 امتیاز تمرین: {u['training_points']}

⛔ سهمیه روزانه: حداکثر {DAILY_SPIRIT_LIMIT} روح و {DAILY_CLEANSE_LIMIT} پاک‌سازی
🍗💧 اگر گرسنه/تشنه شوی مأموریت سخت می‌شود — از فروشگاه بخر
در صورت مرگ: /revive یا آیتم شفا از فروشگاه''',
        reply_markup=main_game_kb()
    )

@router.message(Command('upgrade_coins'))
@router.message(F.text == '💰 ارتقای سکه')
@router.message(F.text == 'ارتقای سکه')
async def upgrade_coins_cmd(message: Message):
    u = await _safe_user(message.from_user.id, message.from_user.full_name)
    if not u:
        return await message.reply('⚠️ خطا در دریافت اطلاعات. دوباره /start بزن.')
    boost = int(u['coin_boost'] or 0) if 'coin_boost' in u.keys() else 0
    bonus = min(boost * 5, 50)
    next_cost_coins = int(500 * (1.6 ** boost)) if boost < 10 else 0
    next_cost_gems = 2 + boost if boost < 10 else 0
    text = (
        f'💰 <b>ارتقای کیف پول / سکه</b>\n\n'
        f'سطح فعلی: <b>{boost}/10</b>\n'
        f'پاداش سکه از مأموریت‌ها: <b>+{bonus}٪</b>\n\n'
    )
    if boost >= 10:
        text += '✅ به حداکثر سطح رسیده‌ای!'
        kb = None
    else:
        text += (
            f'برای ارتقای بعدی نیاز داری:\n'
            f'🪙 {next_cost_coins} سکه\n'
            f'🔮 {next_cost_gems} کریستال سایه\n\n'
            f'موجودی فعلی: 🪙 {u["coins"]} | 🔮 {u["soul_gems"]}'
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f'⬆️ ارتقا به سطح {boost + 1}', callback_data='upgrade_coins_do')]
        ])
    await message.reply(text, reply_markup=kb)


@router.callback_query(F.data == 'upgrade_coins_do')
async def upgrade_coins_do(call: CallbackQuery):
    await _safe_user(call.from_user.id, call.from_user.full_name)
    ok, msg = await upgrade_coin_boost(call.from_user.id)
    await call.answer('ارتقاء انجام شد ✅' if ok else 'ارتقاء ناموفق', show_alert=not ok)
    try:
        await call.message.edit_text(msg if ok else f'❌ {msg}')
    except Exception:
        await call.message.answer(msg if ok else f'❌ {msg}')


@router.message(Command('family'))
@router.message(F.text=='💍 خانواده')
async def family(message:Message):
    u = await _safe_user(message.from_user.id, message.from_user.full_name)
    if not u:
        return await message.reply('⚠️ خطا در دریافت اطلاعات. دوباره /start بزن.')
    marriage = await get_marriage(message.from_user.id)
    children = await list_children(message.from_user.id) or []
    text = '💍 <b>خانواده</b>\n\n'
    if marriage:
        partner_id = marriage['user2_id'] if marriage['user1_id'] == message.from_user.id else marriage['user1_id']
        partner = await get_user(partner_id)
        text += f"💑 همسر: {partner['name'] if partner else partner_id}\n"
    else:
        text += '💍 وضعیت: مجرد\n'
        text += 'برای پیشنهاد ازدواج: /marry شناسه_بازیکن\n'
    text += f"\n👶 فرزندان تحت سرپرستی: {len(children)}\n"
    if children:
        text += '\n'.join(
            f"👶 {c['name']} | سن: {c['age']} | 😊 {c['happiness']}% | ❤️ {c['health']}%"
            for c in children
        )
    text += '\n\nبرای پذیرش فرزند: /adopt نام_کودک'
    await message.reply(text, reply_markup=main_game_kb())


@router.message(Command('marry'))
async def marry(message:Message):
    await _safe_user(message.from_user.id, message.from_user.full_name)
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.reply('💍 استفاده: /marry شناسه_بازیکن')
    ok, msg = await create_marriage_proposal(message.from_user.id, int(parts[1]))
    if not ok:
        return await message.reply('❌ ' + msg)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='💍 قبول', callback_data=f'marry_accept:{message.from_user.id}'),
        InlineKeyboardButton(text='❌ رد', callback_data=f'marry_reject:{message.from_user.id}')
    ]])
    try:
        await message.bot.send_message(
            int(parts[1]),
            f"💍 {message.from_user.full_name} برای ازدواج با تو پیشنهاد فرستاده است.\n\n"
            f"برای تصمیم‌گیری یکی از گزینه‌ها را انتخاب کن.",
            reply_markup=kb
        )
        await message.reply('✅ پیشنهاد ازدواج برای بازیکن موردنظر ارسال شد.')
    except Exception:
        await message.reply(
            '⚠️ پیشنهاد ثبت شد، اما نتوانستم پیام مستقیم برای بازیکن بفرستم. '
            'او باید قبلاً ربات را شروع کرده باشد.'
        )

async def _respond_marriage(call:CallbackQuery, accept:bool):
    try:
        proposer=int(call.data.split(':')[1])
    except Exception:
        return await call.answer('درخواست نامعتبر است.',show_alert=True)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM marriages WHERE user1_id=? AND user2_id=? AND status='pending' ORDER BY id DESC LIMIT 1",
            (proposer, call.from_user.id)
        )
        row = await cur.fetchone()
    if not row:
        return await call.answer('این پیشنهاد دیگر معتبر نیست.',show_alert=True)
    ok=await respond_marriage(row[0],call.from_user.id,accept)
    if not ok:
        return await call.answer('این پیشنهاد دیگر معتبر نیست.',show_alert=True)
    await call.message.edit_text('💍 پیشنهاد ازدواج پذیرفته شد! خانواده شما شکل گرفت. ❤️' if accept else '❌ پیشنهاد ازدواج رد شد.')
    await call.answer('ثبت شد')

@router.callback_query(F.data.startswith('marry_accept:'))
async def marry_accept(call:CallbackQuery):
    await _respond_marriage(call,True)

@router.callback_query(F.data.startswith('marry_reject:'))
async def marry_reject(call:CallbackQuery):
    await _respond_marriage(call,False)

@router.message(Command('adopt'))
async def adopt(message:Message):
    await _safe_user(message.from_user.id, message.from_user.full_name)
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        return await message.reply('👶 استفاده: /adopt نام_کودک')
    ok, name = await adopt_child(message.from_user.id, parts[1])
    if not ok:
        return await message.reply('❌ ' + name)
    await message.reply(
        f'👶 سرپرستی {name} با موفقیت ثبت شد.\n\n'
        f'از بخش «💍 خانواده» می‌توانی وضعیت کودک را ببینی و از او مراقبت کنی.'
    )


@router.callback_query(F.data=='world:family')
async def family_cb(call:CallbackQuery):
    # از call.from_user استفاده می‌کنیم تا کاربر درست شناسایی شود
    u = await _safe_user(call.from_user.id, call.from_user.full_name)
    if not u:
        return await call.answer('⚠️ ابتدا /start را بزن.', show_alert=True)
    marriage = await get_marriage(call.from_user.id)
    children = await list_children(call.from_user.id) or []
    text = '💍 <b>خانواده</b>\n\n'
    if marriage:
        partner_id = marriage['user2_id'] if marriage['user1_id'] == call.from_user.id else marriage['user1_id']
        partner = await get_user(partner_id)
        text += f"💑 همسر: {partner['name'] if partner else partner_id}\n"
    else:
        text += '💍 وضعیت: مجرد\n'
        text += 'برای پیشنهاد ازدواج: /marry شناسه_بازیکن\n'
    text += f"\n👶 فرزندان تحت سرپرستی: {len(children)}\n"
    if children:
        text += '\n'.join(
            f"👶 {c['name']} | سن: {c['age']} | 😊 {c['happiness']}% | ❤️ {c['health']}%"
            for c in children
        )
    text += '\n\nبرای پذیرش فرزند: /adopt نام_کودک'
    try:
        await call.message.edit_text(text, reply_markup=main_game_kb())
    except Exception:
        await call.message.answer(text, reply_markup=main_game_kb())
    await call.answer()


async def _safe_edit(call, text, reply_markup=None):
    try:
        await call.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        await call.message.answer(text, reply_markup=reply_markup)


@router.message(Command('world'))
@router.message(F.text=='🗺️ جهان')
async def world(message:Message):
    u = await _safe_user(message.from_user.id, message.from_user.full_name)
    if not u:
        return await message.reply('⚠️ خطا در دریافت اطلاعات. دوباره /start بزن.')
    rows = await list_regions() or []
    if not rows:
        return await message.reply(
            '🗺️ هنوز منطقه‌ای در جهان ثبت نشده.\n'
            'یک‌بار ربات را ری‌استارت کن تا داده‌های اولیه ساخته شوند.'
        )
    level = int(u['level'] or 1)
    buttons = []
    for r in rows:
        unlock = int(r['unlock_level'] or 1)
        lock = level < unlock
        buttons.append([InlineKeyboardButton(
            text=('🔒 ' if lock else '🗺️ ') + str(r['name']) + f' | سطح {unlock}',
            callback_data=f'region:{r["id"]}'
        )])
    await message.reply(
        '🗺️ <b>جهان راهنمای ارواح</b>\n\n'
        f'سطح تو: <b>{level}</b>\n'
        'هر منطقه داستان‌ها و موجودات مخصوص خودش را دارد.\n'
        'مناطق قفل‌شده با 🔒 مشخص‌اند.',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@router.callback_query(F.data.startswith('region:'))
async def region(call:CallbackQuery):
    u = await _safe_user(call.from_user.id, call.from_user.full_name)
    if not u:
        return await call.answer('⚠️ ابتدا /start را بزن.', show_alert=True)
    try:
        rid = int(call.data.split(':')[1])
    except (ValueError, IndexError):
        return await call.answer('منطقه نامعتبر.', show_alert=True)
    r = await get_region(rid)
    if not r:
        return await call.answer('منطقه پیدا نشد. ربات را ری‌استارت کن.', show_alert=True)
    level = int(u['level'] or 1)
    unlock = int(r['unlock_level'] or 1)
    if level < unlock:
        return await call.answer(f'این منطقه از سطح {unlock} باز می‌شود.', show_alert=True)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='👻 روح‌های منطقه', callback_data=f'rs:{r["id"]}')],
        [InlineKeyboardButton(text='😈 موجودات منطقه', callback_data=f'rd:{r["id"]}')],
        [InlineKeyboardButton(text='🗺️ بازگشت', callback_data='world:regions')]
    ])
    await _safe_edit(call, f"🗺️ <b>{r['name']}</b>\n\n{r['description']}", kb)
    await call.answer()


@router.callback_query(F.data=='world:regions')
async def regions_cb(call:CallbackQuery):
    u = await _safe_user(call.from_user.id, call.from_user.full_name)
    if not u:
        return await call.answer('⚠️ ابتدا /start را بزن.', show_alert=True)
    rows = await list_regions() or []
    level = int(u['level'] or 1)
    if not rows:
        await _safe_edit(call, '🗺️ هنوز منطقه‌ای ثبت نشده. ربات را ری‌استارت کن.')
        return await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=('🔒 ' if level < int(r['unlock_level'] or 1) else '🗺️ ') + str(r['name']),
            callback_data=f'region:{r["id"]}'
        )] for r in rows
    ])
    await _safe_edit(call, f'🗺️ <b>جهان</b>\nسطح تو: {level}', kb)
    await call.answer()


@router.callback_query(F.data.startswith('rs:'))
async def region_spirits(call:CallbackQuery):
    try:
        rid = int(call.data.split(':')[1])
    except (ValueError, IndexError):
        return await call.answer('منطقه نامعتبر.', show_alert=True)
    rows = await list_story_spirits(rid) or []
    buttons = [
        [InlineKeyboardButton(
            text=f"👻 {s['name']} | {'★' * int(s['difficulty'] or 1)}",
            callback_data=f'story:{s["id"]}'
        )] for s in rows
    ]
    buttons.append([InlineKeyboardButton(text='🔙 منطقه', callback_data=f'region:{rid}')])
    text = '👻 <b>دفتر ارواح منطقه</b>' if rows else '👻 در این منطقه هنوز پرونده‌ای نیست.'
    await _safe_edit(call, text, InlineKeyboardMarkup(inline_keyboard=buttons))
    await call.answer()

@router.message(Command('spirits'))
@router.message(F.text=='👻 ارواح')
async def spirits(message:Message):
    await world(message)

@router.callback_query(F.data.startswith('story:'))
async def story(call:CallbackQuery):
    sid=int(call.data.split(':')[1]); s=await get_story_spirit(sid); p=await get_next_clue(call.from_user.id,sid)
    if not s:return await call.answer('پرونده پیدا نشد.',show_alert=True)
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔎 شروع پرونده',callback_data=f'clue:{sid}')],[InlineKeyboardButton(text='🔙 دفتر ارواح',callback_data=f'rs:{s["region_id"]}')]])
    await call.message.edit_text(
        f"👻 <b>{s['name']}</b>\n\n"
        f"نوع: {s['type']}\nسن: {s['age']}\nدرجه: {'★'*s['difficulty']}\n"
        f"منطقه: {s['region_name']}\n\n"
        f"📜 {s['story']}\n\n"
        f"❤️ وضعیت: {s['status']}\n🎯 آخرین خواسته: {s['request']}\n\n"
        f"✨ پاداش پایه: {s['reward_coins']} سکه + {s['reward_xp']} XP\n"
        f"🌟 بدون اشتباه = پایان کامل و پاداش بیشتر",
        reply_markup=kb,
    )
    await call.answer()

@router.callback_query(F.data.startswith('clue:'))
async def clue(call:CallbackQuery):
    ok_alive, msg = await require_alive(call.from_user.id)
    if not ok_alive:
        return await call.answer(msg, show_alert=True)
    sid = int(call.data.split(':')[1])
    s = await get_story_spirit(sid)
    c = await get_next_clue(call.from_user.id, sid)
    if not c:
        await complete_spirit(call, sid, s)
        return
    choices = [c['correct_option']] + ['🚶 ترک منطقه', '💬 سؤال اشتباه', '🌫️ دنبال مه رفتن']
    random.shuffle(choices)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=x, callback_data=f'choice:{sid}:{x}')] for x in choices
    ])
    await call.message.edit_text(
        f"🧩 <b>سرنخ {c['clue_order']}</b>\n\n{c['text']}\n\n"
        f"⚠️ هزینه هر انتخاب: {ENERGY_CLUE} انرژی — انتخاب اشتباه آسیب می‌زند!",
        reply_markup=kb,
    )
    await call.answer()


@router.callback_query(F.data.startswith('choice:'))
async def choice(call:CallbackQuery):
    ok_alive, msg = await require_alive(call.from_user.id)
    if not ok_alive:
        return await call.answer(msg, show_alert=True)
    parts = call.data.split(':', 2)
    if len(parts) < 3:
        return await call.answer('انتخاب نامعتبر.', show_alert=True)
    sid = int(parts[1])
    opt = parts[2]
    s = await get_story_spirit(sid)
    c = await get_next_clue(call.from_user.id, sid)
    if not c:
        return await complete_spirit(call, sid, s)
    if not await spend_energy(call.from_user.id, ENERGY_CLUE):
        return await call.answer(
            f'💠 حداقل {ENERGY_CLUE} انرژی لازم است.', show_alert=True
        )
    ok_need, need_msg = await apply_activity_needs(call.from_user.id, 4, 3)
    if not ok_need:
        return await call.answer(need_msg, show_alert=True)
    correct = opt == c['correct_option']
    ok, idx, done = await advance_spirit(call.from_user.id, sid, correct)
    if not correct:
        alive, hp, died, dmg_msg = await apply_damage(call.from_user.id, DAMAGE_WRONG_CLUE)
        text = (
            f'🌫️ انتخابت اشتباه بود!\n\n{dmg_msg}\n\n'
            f'می‌توانی دوباره تلاش کنی — اگر هنوز زنده‌ای.'
        )
        if died:
            await call.message.edit_text(dmg_msg)
            return await call.answer('مرگ روحی!', show_alert=True)
        await call.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='🔎 ادامه بررسی', callback_data=f'clue:{sid}')]
            ]),
        )
        return await call.answer('سرنخ اشتباه بود.')
    if done:
        return await complete_spirit(call, sid, s)
    await call.message.edit_text(
        f'✨ سرنخ پیدا شد!\n\nپیشرفت پرونده: {idx}/{await clue_count(sid)}',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🔎 سرنخ بعدی', callback_data=f'clue:{sid}')]
        ]),
    )
    await call.answer('درست بود!')


async def clue_count(sid):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute('SELECT COUNT(*) FROM spirit_clues WHERE spirit_id=?', (sid,))
        return (await cur.fetchone())[0]


async def complete_spirit(call, sid, s):
    ok_lim, lim_msg = await check_mission_limit(call.from_user.id, "spirit")
    if not ok_lim:
        await call.message.edit_text(
            f"⛔ پرونده حل شد اما {lim_msg}\n"
            f"پاداش این روح ذخیره نشد. فردا دوباره تلاش کن."
        )
        return await call.answer(lim_msg, show_alert=True)
    # تعداد اشتباهات → نوع پایان
    from database import get_spirit_progress
    progress = await get_spirit_progress(call.from_user.id, sid)
    mistakes = int(progress[2]) if progress and len(progress) > 2 else 0
    if mistakes == 0:
        ending = (
            "🌟 <b>پایان کامل</b>\n"
            f"بدون حتی یک اشتباه، حقیقت {s['name']} را یافتی. "
            "روح با آرامشی نادر از مرز گذشت و نام تو را در نور پسین زمزمه کرد."
        )
        gem_bonus, coin_mul = 2, 1.25
    elif mistakes <= 2:
        ending = (
            "✨ <b>پایان آرام</b>\n"
            f"{s['name']} پس از کمی تردید، حقیقت را پذیرفت و راهی دنیای پسین شد."
        )
        gem_bonus, coin_mul = 1, 1.0
    else:
        ending = (
            "🌫️ <b>پایان تلخ</b>\n"
            f"حقیقت دیر کشف شد. {s['name']} عبور کرد، اما سایه‌ای از پشیمانی با او ماند. "
            "دفعه بعد با دقت بیشتر پیش برو."
        )
        gem_bonus, coin_mul = 0, 0.85

    gems = max(1, int(s['difficulty']) // 2) + gem_bonus
    coins = max(20, int(int(s['reward_coins']) // 2 * coin_mul))
    xp = max(15, int(s['reward_xp']) // 2)
    final_coins, got_gems = await add_progress(
        call.from_user.id, coins, xp, spirit=True, gems=gems
    )
    await bump_mission_limit(call.from_user.id, "spirit")
    light = max(1, int(s['difficulty']))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE users SET light=light+? WHERE user_id=?',
            (light, call.from_user.id),
        )
        await db.commit()
    await call.message.edit_text(
        f"{ending}\n\n"
        f"👻 پرونده: <b>{s['name']}</b>\n"
        f"❌ اشتباهات در مسیر: {mistakes}\n\n"
        f"🪙 +{final_coins} سکه\n✨ +{xp} XP\n"
        f"🔮 +{got_gems} کریستال\n✨ +{light} نور پسین"
    )
    await call.answer('روح راهی شد ✨')

@router.callback_query(F.data=='world:spirits')
async def world_spirits(call:CallbackQuery):
    rows=await list_story_spirits(); kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"👻 {s['name']} | ★{s['difficulty']}",callback_data=f'story:{s["id"]}')] for s in rows]); await call.message.edit_text('👻 <b>دفتر ارواح</b>',reply_markup=kb); await call.answer()

@router.callback_query(F.data.startswith('rd:'))
async def region_demons(call:CallbackQuery):
    try:
        rid = int(call.data.split(':')[1])
    except (ValueError, IndexError):
        return await call.answer('منطقه نامعتبر.', show_alert=True)
    rows = await list_demons(rid) or []
    buttons = [
        [InlineKeyboardButton(
            text=f"😈 {d['name']} | {'★' * int(d['rank'] or 1)}",
            callback_data=f'demon:{d["id"]}'
        )] for d in rows
    ]
    buttons.append([InlineKeyboardButton(text='🔙 منطقه', callback_data=f'region:{rid}')])
    text = '😈 <b>موجودات منطقه</b>' if rows else '😈 در این منطقه موجودی نیست.'
    await _safe_edit(call, text, InlineKeyboardMarkup(inline_keyboard=buttons))
    await call.answer()

@router.message(F.text=='😈 جن‌ها')
@router.message(F.text=='🛡️ پاک‌سازی')
async def demons_message(message:Message):
    await _safe_user(message.from_user.id, message.from_user.full_name)
    rows = await list_demons() or []
    if not rows:
        return await message.reply('😈 هنوز موجودی در دفتر ثبت نشده است.')
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"😈 {d['name']} | {'★'*d['rank']}", callback_data=f"demon:{d['id']}")]
        for d in rows
    ])
    await message.reply(
        '😈 <b>دفتر موجودات و جن‌ها</b>\n\nیکی را انتخاب کن تا پاک‌سازی شروع شود.',
        reply_markup=kb
    )

@router.callback_query(F.data=='world:demons')
async def demons(call:CallbackQuery):
    rows=await list_demons(); kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"😈 {d['name']} | {'★'*d['rank']}",callback_data=f'demon:{d["id"]}')] for d in rows]); await call.message.edit_text('😈 <b>دفتر موجودات</b>',reply_markup=kb); await call.answer()

@router.callback_query(F.data.startswith('demon:'))
async def demon(call: CallbackQuery):
    did = int(call.data.split(':')[1])
    d = await get_demon(did)
    if not d:
        return await call.answer('موجود پیدا نشد.', show_alert=True)
    e = await get_or_create_encounter(call.from_user.id, did)
    status = e['status'] if e else 'active'
    buttons = []
    if status == 'completed':
        buttons.append([InlineKeyboardButton(text='🔄 مبارزه دوباره (۵ انرژی)', callback_data=f'dreset:{did}')])
    else:
        buttons.extend([
            [InlineKeyboardButton(text='🔍 بررسی آلودگی', callback_data=f'dcheck:{did}')],
            [InlineKeyboardButton(text='🔮 مهر محافظ', callback_data=f'dseal:{did}')],
            [InlineKeyboardButton(text='🕯️ پاک‌سازی', callback_data=f'dclean:{did}')],
        ])
    buttons.append([InlineKeyboardButton(text='🏃 عقب‌نشینی', callback_data='world:demons')])
    hp_show = e['health'] if e else d['health']
    corr_show = e['corruption'] if e else d['corruption']
    await call.message.edit_text(
        f"😈 <b>{d['name']}</b>\n\n"
        f"نوع: {d['type']}\nرتبه: {'★'*d['rank']}\nمنطقه: {d['region_name']}\n"
        f"❤️ سلامت: {hp_show}\n☠️ آلودگی: {corr_show}٪\n🛡️ دفاع: {d['defense']}\n"
        f"وضعیت: {'✅ پاک‌سازی‌شده' if status == 'completed' else '⚔️ فعال'}\n\n"
        f"📜 {d['story']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await call.answer()

@router.callback_query(F.data.startswith('dcheck:'))
async def dcheck(call: CallbackQuery):
    did = int(call.data.split(':')[1])
    e = await get_or_create_encounter(call.from_user.id, did)
    if not e:
        return await call.answer('موجود پیدا نشد.', show_alert=True)
    status = e['status'] if 'status' in e.keys() else 'active'
    await call.answer(
        f"☠️ آلودگی: {e['corruption']}٪ | ❤️ سلامت: {e['health']} | وضعیت: {status}",
        show_alert=True
    )

@router.callback_query(F.data.startswith('dseal:'))
async def dseal(call: CallbackQuery):
    ok_alive, msg = await require_alive(call.from_user.id)
    if not ok_alive:
        return await call.answer(msg, show_alert=True)
    did = int(call.data.split(':')[1])
    d = await get_demon(did)
    e = await get_or_create_encounter(call.from_user.id, did)
    if not d or not e:
        return await call.answer('موجود پیدا نشد.', show_alert=True)
    if e['status'] == 'completed':
        return await call.answer('این موجود قبلاً پاک‌سازی شده. از «مبارزه دوباره» استفاده کن.', show_alert=True)
    if not await spend_energy(call.from_user.id, ENERGY_SEAL):
        return await call.answer(f'💠 حداقل {ENERGY_SEAL} انرژی لازم است.', show_alert=True)
    # آسیب متقابل از جن
    dmg = random.randint(DAMAGE_DEMON_HIT_MIN, DAMAGE_DEMON_HIT_MAX // 2)
    alive, php, died, dmg_msg = await apply_damage(call.from_user.id, dmg)
    if died:
        await call.message.edit_text(dmg_msg)
        return await call.answer('مرگ روحی در نبرد!', show_alert=True)
    corr = max(0, e['corruption'] - random.randint(4, 10))
    hp = max(0, e['health'] - random.randint(5, 15))
    await update_encounter(call.from_user.id, did, hp, corr, e['stage'])
    await call.message.edit_text(
        f'🔮 مهر محافظ فعال شد!\n\n☠️ آلودگی: {corr}%\n❤️ سلامت موجود: {hp}\n{dmg_msg}',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🕯️ ادامه پاک‌سازی', callback_data=f'dclean:{did}')]
        ])
    )
    await call.answer('آلودگی کمی کاهش یافت.')


@router.callback_query(F.data.startswith('dclean:'))
async def dclean(call: CallbackQuery):
    ok_alive, msg = await require_alive(call.from_user.id)
    if not ok_alive:
        return await call.answer(msg, show_alert=True)
    did = int(call.data.split(':')[1])
    d = await get_demon(did)
    e = await get_or_create_encounter(call.from_user.id, did)
    if not d or not e:
        return await call.answer('موجود پیدا نشد.', show_alert=True)
    if e['status'] == 'completed':
        return await call.answer('این موجود قبلاً پاک‌سازی شده. از «مبارزه دوباره» استفاده کن.', show_alert=True)
    if not await spend_energy(call.from_user.id, ENERGY_CLEAN):
        return await call.answer(f'💠 حداقل {ENERGY_CLEAN} انرژی لازم است.', show_alert=True)
    dmg = random.randint(DAMAGE_DEMON_HIT_MIN, DAMAGE_DEMON_HIT_MAX)
    alive, php, died, dmg_msg = await apply_damage(call.from_user.id, dmg)
    if died:
        await call.message.edit_text(dmg_msg)
        return await call.answer('مرگ روحی در نبرد!', show_alert=True)
    corr = max(0, e['corruption'] - random.randint(5, 12))
    hp = max(0, e['health'] - random.randint(8, 22))
    if corr == 0:
        ok_lim, lim_msg = await check_mission_limit(call.from_user.id, "cleanse")
        if not ok_lim:
            await update_encounter(call.from_user.id, did, hp, corr, e['stage'], 'completed')
            await call.message.edit_text(
                f'✨ پاک‌سازی کامل شد اما {lim_msg}\nپاداش داده نشد.'
            )
            return await call.answer(lim_msg, show_alert=True)
        await update_encounter(call.from_user.id, did, hp, corr, e['stage'], 'completed')
        gems = max(1, int(d['rank']) // 2)
        coins = max(30, int(d['reward_coins']) // 2)
        xp = max(20, int(d['reward_xp']) // 2)
        final_coins, got_gems = await add_progress(
            call.from_user.id, coins, xp, cleanse=True, gems=gems
        )
        await bump_mission_limit(call.from_user.id, "cleanse")
        await call.message.edit_text(
            f'✨ <b>پاک‌سازی کامل شد!</b>\n\n'
            f'😈 {d["name"]} از آلودگی رها شد.\n'
            f'🪙 +{final_coins} سکه\n✨ +{xp} XP\n'
            f'🔮 +{got_gems} کریستال\n{dmg_msg}\n\n'
            f'می‌توانی بعداً دوباره مبارزه کنی (هزینه بالا).',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f'🔄 مبارزه دوباره ({ENERGY_RESET} انرژی)',
                    callback_data=f'dreset:{did}'
                )],
                [InlineKeyboardButton(text='🔙 دفتر جن‌ها', callback_data='world:demons')]
            ])
        )
        return await call.answer('پاک‌سازی کامل شد!')
    await update_encounter(call.from_user.id, did, hp, corr, e['stage'] + 1)
    await call.message.edit_text(
        f'🕯️ مرحله پاک‌سازی انجام شد.\n\n'
        f'☠️ آلودگی باقی‌مانده: {corr}%\n❤️ سلامت موجود: {hp}\n{dmg_msg}',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text='🔮 مهر محافظ', callback_data=f'dseal:{did}'),
                InlineKeyboardButton(text='🕯️ پاک‌سازی بعدی', callback_data=f'dclean:{did}')
            ]
        ])
    )
    await call.answer('ادامه بده — مراقب سلامتی‌ات باش!')


@router.callback_query(F.data.startswith('dreset:'))
async def dreset(call: CallbackQuery):
    ok_alive, msg = await require_alive(call.from_user.id)
    if not ok_alive:
        return await call.answer(msg, show_alert=True)
    did = int(call.data.split(':')[1])
    d = await get_demon(did)
    if not d:
        return await call.answer('موجود پیدا نشد.', show_alert=True)
    if not await spend_energy(call.from_user.id, ENERGY_RESET):
        return await call.answer(f'💠 برای مبارزه دوباره به {ENERGY_RESET} انرژی نیاز داری.', show_alert=True)
    await reset_encounter(call.from_user.id, did)
    e = await get_or_create_encounter(call.from_user.id, did)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔍 بررسی آلودگی', callback_data=f'dcheck:{did}')],
        [InlineKeyboardButton(text='🔮 مهر محافظ', callback_data=f'dseal:{did}')],
        [InlineKeyboardButton(text='🕯️ پاک‌سازی', callback_data=f'dclean:{did}')],
        [InlineKeyboardButton(text='🏃 عقب‌نشینی', callback_data='world:demons')]
    ])
    await call.message.edit_text(
        f"🔄 <b>مبارزه دوباره با {d['name']}</b>\n\n"
        f"نوع: {d['type']}\nرتبه: {'★'*d['rank']}\n"
        f"❤️ سلامت: {e['health']}\n☠️ آلودگی: {e['corruption']}٪\n\n"
        f"📜 {d['story']}",
        reply_markup=kb
    )
    await call.answer('مبارزه از نو شروع شد!')


@router.message(Command("balance"))
@router.message(F.text == "💰 موجودی")
async def balance_cmd(message: Message):
    u = await _safe_user(message.from_user.id, message.from_user.full_name)
    if not u:
        return await message.reply('⚠️ خطا در دریافت موجودی. دوباره /start بزن.')
    boost = int(u["coin_boost"] or 0) if "coin_boost" in u.keys() else 0
    bonus = min(boost * 5, 50)
    await message.reply(
        f"💰 <b>موجودی</b>\n\n"
        f"🪙 سکه: {u['coins']}\n"
        f"🔮 کریستال سایه: {u['soul_gems']}\n"
        f"💠 انرژی: {u['energy']}\n"
        f"✨ نور پسین: {u['light'] if 'light' in u.keys() else 0}\n"
        f"💰 ارتقای سکه: سطح {boost}/10 (+{bonus}٪)\n\n"
        f"برای ارتقا از دکمه «💰 ارتقای سکه» استفاده کن."
    )


@router.message(Command('daily'))
@router.message(F.text=='🎁 جایزه روزانه')
async def daily(message:Message):
    u = await _safe_user(message.from_user.id, message.from_user.full_name)
    if not u:
        return await message.reply('⚠️ خطا در دریافت اطلاعات. دوباره /start بزن.')
    ok, msg = await daily_claim(message.from_user.id)
    if ok:
        await message.reply(msg)
    else:
        await message.reply(f'⏳ {msg}')

@router.message(Command('shop'))
@router.message(F.text=='🛒 فروشگاه')
async def shop(message:Message):
    await _safe_user(message.from_user.id, message.from_user.full_name)
    rows = await list_shop_items() or []
    if not rows:
        return await message.reply('🛒 فروشگاه فعلاً خالی است.')
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{r['name']} | 🪙{r['price_coins']} 💎{r['price_gems']}",
            callback_data=f'shop:{r["id"]}'
        )] for r in rows
    ])
    await message.reply('🛒 <b>فروشگاه محافظان</b>\n\nآیتم موردنظر را انتخاب کن:', reply_markup=kb)

@router.callback_query(F.data.startswith('shop:'))
async def shop_detail(call:CallbackQuery):
    try:
        item_id = int(call.data.split(':')[1])
    except (ValueError, IndexError):
        return await call.answer('آیتم نامعتبر است.', show_alert=True)
    item = await get_shop_item(item_id)
    if not item:
        return await call.answer('آیتم پیدا نشد.', show_alert=True)
    effects = []
    if item['energy_gain']:
        effects.append(f"💠 +{item['energy_gain']} انرژی (با استفاده)")
    if item['mission_bonus']:
        effects.append(f"🔮 +{item['mission_bonus']} قدرت روح (با استفاده)")
    effect_line = "\n".join(effects) if effects else "اثر ویژه هنگام استفاده"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🛒 خرید', callback_data=f'buy:{item["id"]}')],
        [InlineKeyboardButton(text='🔙 فروشگاه', callback_data='shopback')]
    ])
    await call.message.edit_text(
        f"<b>{item['name']}</b>\n\n"
        f"{item['description']}\n\n"
        f"🪙 قیمت سکه: {item['price_coins']}\n"
        f"💎 قیمت کریستال: {item['price_gems']}\n"
        f"📦 تعداد در هر خرید: {item['quantity'] or 1}\n\n"
        f"{effect_line}",
        reply_markup=kb
    )
    await call.answer()

@router.callback_query(F.data.startswith('buy:'))
async def buy(call:CallbackQuery):
    await ensure_user(call.from_user.id, call.from_user.full_name)
    try:
        item_id = int(call.data.split(':')[1])
    except (ValueError, IndexError):
        return await call.answer('آیتم نامعتبر است.', show_alert=True)
    ok, res = await buy_shop_item(call.from_user.id, item_id)
    if ok:
        await call.answer('خرید انجام شد 🛒', show_alert=False)
        await call.message.edit_text(
            f"✅ <b>{res['name']}</b> به کوله‌پشتی اضافه شد.\n\n"
            f"از بخش 🎒 کوله‌پشتی می‌توانی آن را استفاده کنی.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='🎒 کوله‌پشتی', callback_data='world:inventory')],
                [InlineKeyboardButton(text='🔙 فروشگاه', callback_data='shopback')]
            ])
        )
    else:
        msg = {
            'item_not_found': 'آیتم پیدا نشد.',
            'user_not_found': 'کاربر پیدا نشد.',
            'not_enough': 'سکه یا کریستال کافی نیست.',
        }.get(res, 'خرید ناموفق بود.')
        await call.answer(msg, show_alert=True)

@router.callback_query(F.data=='shopback')
async def shopback(call:CallbackQuery):
    rows = await list_shop_items()
    if not rows:
        await call.message.edit_text('🛒 فروشگاه فعلاً خالی است.')
        return await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{r['name']} | 🪙{r['price_coins']} 💎{r['price_gems']}",
            callback_data=f'shop:{r["id"]}'
        )] for r in rows
    ])
    await call.message.edit_text('🛒 <b>فروشگاه محافظان</b>\n\nآیتم موردنظر را انتخاب کن:', reply_markup=kb)
    await call.answer()

def inventory_markup(rows):
    buttons = []
    for r in rows:
        buttons.append([InlineKeyboardButton(text=f"🧪 استفاده: {r['name']} × {r['quantity']}", callback_data=f"useitem:{r['item_id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None

async def render_inventory_message(message: Message, edit=False):
    rows = await get_inventory(message.from_user.id)
    text = '🎒 <b>کوله‌پشتی</b>\n\n' + (''.join(f"{r['name']} × {r['quantity']}\n📝 {r['description']}\n\n" for r in rows) if rows else 'خالی است.')
    kb = inventory_markup(rows)
    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.reply(text, reply_markup=kb, reply_to_message_id=message.message_id)

@router.message(Command('inventory'))
@router.message(F.text=='🎒 کوله‌پشتی')
async def inventory(message:Message):
    u = await _safe_user(message.from_user.id, message.from_user.full_name)
    if not u:
        return await message.reply('⚠️ خطا در دریافت اطلاعات. دوباره /start بزن.')
    await render_inventory_message(message)


@router.callback_query(F.data=='world:inventory')
async def inventory_cb(call:CallbackQuery):
    await _safe_user(call.from_user.id, call.from_user.full_name)
    rows = await get_inventory(call.from_user.id) or []
    text = '🎒 <b>کوله‌پشتی</b>\n\n' + (
        ''.join(f"{r['name']} × {r['quantity']}\n📝 {r['description']}\n\n" for r in rows)
        if rows else 'خالی است.'
    )
    try:
        await call.message.edit_text(text, reply_markup=inventory_markup(rows))
    except Exception:
        await call.message.answer(text, reply_markup=inventory_markup(rows))
    await call.answer()

@router.callback_query(F.data.startswith('useitem:'))
async def use_item(call:CallbackQuery):
    try:
        item_id = int(call.data.split(':', 1)[1])
    except (ValueError, IndexError):
        return await call.answer('آیتم نامعتبر است.', show_alert=True)
    await ensure_user(call.from_user.id, call.from_user.full_name)
    ok, result = await use_inventory_item(call.from_user.id, item_id)
    if not ok:
        return await call.answer(result, show_alert=True)
    item = result['item']
    await call.answer(f"{item['name']} مصرف شد.", show_alert=False)
    await call.message.reply(
        f"🧪 <b>آیتم استفاده شد</b>\n\n{item['name']}\n{result['effect']}\n📦 باقی‌مانده: {result['remaining']}",
        reply_markup=inventory_markup(await get_inventory(call.from_user.id))
    )

@router.message(Command('rank'))
@router.message(F.text=='🏆 رتبه‌بندی')
async def rank(message:Message):
    await _safe_user(message.from_user.id, message.from_user.full_name)
    season_id, season_rows = await top_season(10)
    all_rows = await top_users() or []
    text = f'🏆 <b>رتبه‌بندی فصلی</b> ({season_id})\n'
    text += 'امتیاز از راهنمایی روح و پاک‌سازی جن — هر ماه ریست می‌شود.\n\n'
    if season_rows:
        text += ''.join(
            f"{i}. {r['name']} — ⭐ {r['level']} | 🏅 {r['points']} امتیاز\n"
            for i, r in enumerate(season_rows, 1)
        )
    else:
        text += 'هنوز کسی در این فصل امتیازی ندارد.\n'
    text += '\n📜 <b>تالار همیشگی</b>\n'
    if all_rows:
        text += ''.join(
            f"{i}. {r['name']} — سطح {r['level']} | 👻 {r['spirits_sent']} | 😈 {r['cleanses']}\n"
            for i, r in enumerate(all_rows, 1)
        )
    else:
        text += 'خالی است.'
    await message.reply(text)


def _missions_text_and_kb(missions):
    day = missions[0].get("day", "") if missions else ""
    lines = [
        "📜 <b>مأموریت‌های روزانه کریستال</b>",
        f"📅 امروز: <code>{day}</code>",
        "پیشرفت فقط با انجام کارها زیاد می‌شود و با باز کردن این صفحه پاک نمی‌شود.",
        "هر نیمه‌شب (به وقت ایران) مأموریت‌ها عوض می‌شوند.\n",
    ]
    buttons = []
    for m in missions:
        if m["claimed"]:
            status = "✅ دریافت‌شده"
        elif m["done"]:
            status = "🎁 آماده دریافت"
        else:
            status = f"⏳ {m['progress']}/{m['target']}"
        lines.append(f"{m['title']}\n   {status} · پاداش: 🔮 {m['reward_gems']}")
        if m["done"] and not m["claimed"]:
            buttons.append([InlineKeyboardButton(
                text=f"🎁 دریافت پاداش",
                callback_data=f"missions:claim:{m['key']}",
            )])
    buttons.append([InlineKeyboardButton(text="🔄 بروزرسانی", callback_data="missions:list")])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("missions"))
@router.message(F.text == "📜 مأموریت‌ها")
async def missions_cmd(message: Message):
    await _safe_user(message.from_user.id, message.from_user.full_name)
    missions = await get_daily_missions(message.from_user.id)
    text, kb = _missions_text_and_kb(missions)
    await message.reply(text, reply_markup=kb)


@router.callback_query(F.data == "missions:list")
async def missions_list_cb(call: CallbackQuery):
    await _safe_user(call.from_user.id, call.from_user.full_name)
    missions = await get_daily_missions(call.from_user.id)
    text, kb = _missions_text_and_kb(missions)
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)
    try:
        await call.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("missions:claim:"))
async def missions_claim_cb(call: CallbackQuery):
    await _safe_user(call.from_user.id, call.from_user.full_name)
    key = call.data.split(":", 2)[2]
    ok, msg = await claim_mission_reward(call.from_user.id, key)
    try:
        await call.answer(msg, show_alert=True)
    except Exception:
        pass
    # همیشه لیست را از دیتابیس دوباره بخوان (ریست نمی‌شود)
    missions = await get_daily_missions(call.from_user.id)
    text, kb = _missions_text_and_kb(missions)
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)


@router.message(Command('revive'))
async def revive_cmd(message: Message):
    await _safe_user(message.from_user.id, message.from_user.full_name)
    ok, msg = await revive_with_gems(message.from_user.id, 5)
    await message.reply(msg if ok else f'❌ {msg}')


@router.message(Command('heal'))
@router.message(F.text == '❤️ شفا')
async def heal_cmd(message: Message):
    """شفا با سکه (گرون و کم‌اثر — نسخه سخت)."""
    u = await _safe_user(message.from_user.id, message.from_user.full_name)
    if not u:
        return await message.reply('⚠️ دوباره /start بزن.')
    cost = 80
    if int(u['coins'] or 0) < cost:
        return await message.reply(f'🪙 برای شفا نیاز به {cost} سکه داری.')
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET coins=coins-? WHERE user_id=?", (cost, message.from_user.id)
        )
        await db.commit()
    ok, hp, msg = await heal_user(message.from_user.id, 20)
    await message.reply(f'{"✅" if ok else "❌"} {msg}\n🪙 -{cost} سکه')
