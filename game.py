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
    adopt_child, care_for_child, train_mind, get_training_stats, DB_PATH
)
import aiosqlite

router=Router()

def main_game_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='👻 دفتر ارواح',callback_data='world:spirits'),InlineKeyboardButton(text='😈 جن‌ها',callback_data='world:demons')],
        [InlineKeyboardButton(text='🗺️ جهان',callback_data='world:regions'),InlineKeyboardButton(text='🎒 کوله‌پشتی',callback_data='world:inventory')],
        [InlineKeyboardButton(text='💍 خانواده',callback_data='world:family'),InlineKeyboardButton(text='🧠 پرورش ذهن',callback_data='training:mind')],
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
    await message.reply(
        f'''👤 <b>پروفایل راهنمای ارواح</b>

نام: {u['name']}
⭐ سطح راهنمایی: {u['level']}
✨ تجربه: {u['xp']}
❤️ سلامتی: {u['health']}/{u['max_health']}
💠 انرژی روحی: {u['energy']}
🪙 سکه: {u['coins']}
🔮 کریستال سایه: {u['soul_gems']}
✨ نور پسین: {u.get('light') or 0}
💰 ارتقای سکه: سطح {boost}/10 (+{bonus}٪ پاداش)
👻 ارواح راهی‌شده: {u['spirits_sent']}
😈 پاک‌سازی‌ها: {u['cleanses']}
🧠 قدرت ذهن: {u['mind_power']}
💪 قدرت جسم: {u['body_power']}
🔮 قدرت روح: {u['spirit_power']}
🏅 امتیاز تمرین: {u['training_points']}''',
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


@router.message(Command('world'))
@router.message(F.text=='🗺️ جهان')
async def world(message:Message):
    u = await _safe_user(message.from_user.id, message.from_user.full_name)
    if not u:
        return await message.reply('⚠️ خطا در دریافت اطلاعات. دوباره /start بزن.')
    rows = await list_regions() or []
    buttons = []
    for r in rows:
        lock = u['level'] < r['unlock_level']
        buttons.append([InlineKeyboardButton(
            text=('🔒 ' if lock else '🗺️ ') + r['name'] + f' | سطح {r["unlock_level"]}',
            callback_data=f'region:{r["id"]}'
        )])
    await message.reply(
        '🗺️ <b>جهان راهنمای ارواح</b>\n\nهر منطقه داستان‌ها و موجودات مخصوص خودش را دارد.',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
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
        return await call.answer('منطقه پیدا نشد.', show_alert=True)
    if u['level'] < r['unlock_level']:
        return await call.answer(f'این منطقه از سطح {r["unlock_level"]} باز می‌شود.', show_alert=True)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='👻 روح‌های منطقه', callback_data=f'rs:{r["id"]}')],
        [InlineKeyboardButton(text='😈 موجودات منطقه', callback_data=f'rd:{r["id"]}')],
        [InlineKeyboardButton(text='🗺️ بازگشت', callback_data='world:regions')]
    ])
    await call.message.edit_text(f"🗺️ <b>{r['name']}</b>\n\n{r['description']}", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data=='world:regions')
async def regions_cb(call:CallbackQuery):
    u = await _safe_user(call.from_user.id, call.from_user.full_name)
    if not u:
        return await call.answer('⚠️ ابتدا /start را بزن.', show_alert=True)
    rows = await list_regions() or []
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=('🔒 ' if u['level'] < r['unlock_level'] else '🗺️ ') + r['name'],
            callback_data=f'region:{r["id"]}'
        )] for r in rows
    ])
    await call.message.edit_text('🗺️ <b>جهان</b>', reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith('rs:'))
async def region_spirits(call:CallbackQuery):
    rid=int(call.data.split(':')[1]); rows=await list_story_spirits(rid)
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"👻 {s['name']} | {'★'*s['difficulty']}",callback_data=f'story:{s["id"]}')] for s in rows]+[[InlineKeyboardButton(text='🔙 منطقه',callback_data=f'region:{rid}')]])
    await call.message.edit_text('👻 <b>دفتر ارواح منطقه</b>',reply_markup=kb); await call.answer()

@router.message(Command('spirits'))
@router.message(F.text=='👻 ارواح')
@router.message(F.text=='📜 مأموریت‌ها')
async def spirits(message:Message):
    await world(message)

@router.callback_query(F.data.startswith('story:'))
async def story(call:CallbackQuery):
    sid=int(call.data.split(':')[1]); s=await get_story_spirit(sid); p=await get_next_clue(call.from_user.id,sid)
    if not s:return await call.answer('پرونده پیدا نشد.',show_alert=True)
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔎 شروع پرونده',callback_data=f'clue:{sid}')],[InlineKeyboardButton(text='🔙 دفتر ارواح',callback_data=f'rs:{s["region_id"]}')]])
    await call.message.edit_text(f"👻 <b>{s['name']}</b>\n\nنوع: {s['type']}\nسن: {s['age']}\nدرجه: {'★'*s['difficulty']}\nمنطقه: {s['region_name']}\n\n📜 {s['story']}\n\n❤️ وضعیت: {s['status']}\n🎯 آخرین خواسته: {s['request']}\n\n✨ پاداش: {s['reward_coins']} سکه + {s['reward_xp']} XP",reply_markup=kb); await call.answer()

@router.callback_query(F.data.startswith('clue:'))
async def clue(call:CallbackQuery):
    sid=int(call.data.split(':')[1]); s=await get_story_spirit(sid); c=await get_next_clue(call.from_user.id,sid)
    if not c:
        await complete_spirit(call,sid,s); return
    # Three choices, one correct; wrong choices keep story open but cost energy.
    choices=[c['correct_option']]+['🚶 ترک منطقه','💬 سؤال اشتباه']
    random.shuffle(choices)
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=x,callback_data=f'choice:{sid}:{x}')] for x in choices])
    await call.message.edit_text(f"🧩 <b>سرنخ {c['clue_order']}</b>\n\n{c['text']}\n\nچه می‌کنی؟",reply_markup=kb); await call.answer()

@router.callback_query(F.data.startswith('choice:'))
async def choice(call:CallbackQuery):
    _,sid,opt=call.data.split(':',2); sid=int(sid); s=await get_story_spirit(sid); c=await get_next_clue(call.from_user.id,sid); u=await get_user(call.from_user.id)
    if not await spend_energy(call.from_user.id, 1):
        return await call.answer('💠 انرژی روحی کافی نداری.', show_alert=True)
    correct = opt == c['correct_option']
    ok, idx, done = await advance_spirit(call.from_user.id, sid, correct)
    if not correct:
        await call.message.edit_text('🌫️ انتخابت سرنخ را کامل نکرد.\n\nمی‌توانی دوباره بررسی کنی.',reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔎 ادامه بررسی',callback_data=f'clue:{sid}')]])); return await call.answer('سرنخ اشتباه بود.')
    if done:return await complete_spirit(call,sid,s)
    await call.message.edit_text(f'✨ سرنخ پیدا شد!\n\nپیشرفت پرونده: {idx}/{await clue_count(sid)}',reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔎 سرنخ بعدی',callback_data=f'clue:{sid}')]])); await call.answer('درست بود!')

async def clue_count(sid):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute('SELECT COUNT(*) FROM spirit_clues WHERE spirit_id=?', (sid,))
        return (await cur.fetchone())[0]

async def complete_spirit(call, sid, s):
    final_coins = await add_progress(call.from_user.id, s['reward_coins'], s['reward_xp'], spirit=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE users SET light=light+? WHERE user_id=?',
            (max(1, s['difficulty'] * 2), call.from_user.id)
        )
        await db.commit()
    await call.message.edit_text(
        f"✨ <b>روح آرام گرفت</b>\n\n"
        f"👻 {s['name']} حقیقت را یافت و از مرز میان دو دنیا عبور کرد.\n\n"
        f"🪙 +{final_coins} سکه\n✨ +{s['reward_xp']} XP\n"
        f"✨ +{max(1, s['difficulty'] * 2)} نور پسین"
    )
    await call.answer('روح راهی شد ✨')

@router.callback_query(F.data=='world:spirits')
async def world_spirits(call:CallbackQuery):
    rows=await list_story_spirits(); kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"👻 {s['name']} | ★{s['difficulty']}",callback_data=f'story:{s["id"]}')] for s in rows]); await call.message.edit_text('👻 <b>دفتر ارواح</b>',reply_markup=kb); await call.answer()

@router.callback_query(F.data.startswith('rd:'))
async def region_demons(call:CallbackQuery):
    rid=int(call.data.split(':')[1]); rows=await list_demons(rid); kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"😈 {d['name']} | {'★'*d['rank']}",callback_data=f'demon:{d["id"]}')] for d in rows]+[[InlineKeyboardButton(text='🔙 منطقه',callback_data=f'region:{rid}')]])
    await call.message.edit_text('😈 <b>موجودات منطقه</b>',reply_markup=kb); await call.answer()

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
    did = int(call.data.split(':')[1])
    d = await get_demon(did)
    e = await get_or_create_encounter(call.from_user.id, did)
    if not d or not e:
        return await call.answer('موجود پیدا نشد.', show_alert=True)
    if e['status'] == 'completed':
        return await call.answer('این موجود قبلاً پاک‌سازی شده. از «مبارزه دوباره» استفاده کن.', show_alert=True)
    if not await spend_energy(call.from_user.id, 2):
        return await call.answer('💠 انرژی کافی نداری.', show_alert=True)
    corr = max(0, e['corruption'] - random.randint(12, 24))
    hp = max(0, e['health'] - random.randint(10, 35))
    await update_encounter(call.from_user.id, did, hp, corr, e['stage'])
    await call.message.edit_text(
        f'🔮 مهر محافظ فعال شد!\n\n☠️ آلودگی: {corr}%\n❤️ سلامت: {hp}',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🕯️ ادامه پاک‌سازی', callback_data=f'dclean:{did}')]
        ])
    )
    await call.answer('آلودگی کاهش یافت.')

@router.callback_query(F.data.startswith('dclean:'))
async def dclean(call: CallbackQuery):
    did = int(call.data.split(':')[1])
    d = await get_demon(did)
    e = await get_or_create_encounter(call.from_user.id, did)
    if not d or not e:
        return await call.answer('موجود پیدا نشد.', show_alert=True)
    if e['status'] == 'completed':
        return await call.answer('این موجود قبلاً پاک‌سازی شده. از «مبارزه دوباره» استفاده کن.', show_alert=True)
    if not await spend_energy(call.from_user.id, 2):
        return await call.answer('💠 انرژی کافی نداری.', show_alert=True)
    corr = max(0, e['corruption'] - random.randint(15, 30))
    hp = max(0, e['health'] - random.randint(20, 55))
    if corr == 0:
        await update_encounter(call.from_user.id, did, hp, corr, e['stage'], 'completed')
        final_coins = await add_progress(call.from_user.id, d['reward_coins'], d['reward_xp'], cleanse=True)
        await call.message.edit_text(
            f'✨ <b>پاک‌سازی کامل شد!</b>\n\n'
            f'😈 {d["name"]} از آلودگی رها شد.\n'
            f'🪙 +{final_coins} سکه\n✨ +{d["reward_xp"]} XP\n\n'
            f'می‌توانی بعداً دوباره با او مبارزه کنی.',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='🔄 مبارزه دوباره (۵ انرژی)', callback_data=f'dreset:{did}')],
                [InlineKeyboardButton(text='🔙 دفتر جن‌ها', callback_data='world:demons')]
            ])
        )
        return await call.answer('پاک‌سازی کامل شد!')
    await update_encounter(call.from_user.id, did, hp, corr, e['stage'] + 1)
    await call.message.edit_text(
        f'🕯️ مرحله پاک‌سازی انجام شد.\n\n'
        f'☠️ آلودگی باقی‌مانده: {corr}%\n❤️ سلامت موجود: {hp}',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text='🔮 مهر محافظ', callback_data=f'dseal:{did}'),
                InlineKeyboardButton(text='🕯️ پاک‌سازی بعدی', callback_data=f'dclean:{did}')
            ]
        ])
    )
    await call.answer('ادامه بده!')

@router.callback_query(F.data.startswith('dreset:'))
async def dreset(call: CallbackQuery):
    did = int(call.data.split(':')[1])
    d = await get_demon(did)
    if not d:
        return await call.answer('موجود پیدا نشد.', show_alert=True)
    if not await spend_energy(call.from_user.id, 5):
        return await call.answer('💠 برای مبارزه دوباره به ۵ انرژی نیاز داری.', show_alert=True)
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
    rows = await top_users() or []
    if not rows:
        return await message.reply('🏆 هنوز کسی در رتبه‌بندی نیست.')
    text = '🏆 <b>تالار راهنمایان</b>\n\n' + ''.join(
        f"{i}. {r['name']} — سطح {r['level']} | 👻 {r['spirits_sent']} | 😈 {r['cleanses']}\n"
        for i, r in enumerate(rows, 1)
    )
    await message.reply(text)
