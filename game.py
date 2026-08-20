import random
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import (ensure_user,get_user,top_users,daily_claim,list_shop_items,get_shop_item,buy_shop_item,get_inventory,
    list_regions,get_region,list_story_spirits,get_story_spirit,get_next_clue,advance_spirit,list_demons,get_demon,get_or_create_encounter,update_encounter,add_progress,
    create_marriage_proposal,get_pending_proposal,respond_marriage,get_marriage,list_children,adopt_child,care_for_child)

router=Router()

def main_game_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='👻 دفتر ارواح',callback_data='world:spirits'),InlineKeyboardButton(text='😈 جن‌ها',callback_data='world:demons')],
        [InlineKeyboardButton(text='🗺️ جهان',callback_data='world:regions'),InlineKeyboardButton(text='🎒 کوله‌پشتی',callback_data='world:inventory')],
        [InlineKeyboardButton(text='💍 خانواده',callback_data='world:family')],
    ])

@router.message(Command('profile'))
@router.message(F.text=='👤 پروفایل')
async def profile(message:Message):
    await ensure_user(message.from_user.id,message.from_user.full_name); u=await get_user(message.from_user.id)
    await message.answer(f'''👤 <b>پروفایل راهنمای ارواح</b>\n\nنام: {u['name']}\n⭐ سطح راهنمایی: {u['level']}\n✨ تجربه: {u['xp']}\n❤️ سلامتی: {u['health']}/{u['max_health']}\n💠 انرژی روحی: {u['energy']}\n🪙 سکه: {u['coins']}\n🔮 کریستال سایه: {u['soul_gems']}\n✨ نور پسین: {u['light']}\n👻 ارواح راهی‌شده: {u['spirits_sent']}\n😈 پاک‌سازی‌ها: {u['cleanses']}''',reply_markup=main_game_kb())

@router.message(Command('family'))
@router.message(F.text=='💍 خانواده')
async def family(message:Message):
    u=await get_user(message.from_user.id)
    marriage=await get_marriage(message.from_user.id)
    children=await list_children(message.from_user.id)
    text='💍 <b>خانواده</b>\n\n'
    if marriage:
        partner_id=marriage['user2_id'] if marriage['user1_id']==message.from_user.id else marriage['user1_id']
        partner=await get_user(partner_id)
        text+=f"💑 همسر: {partner['name'] if partner else partner_id}\n"
    else:
        text+='💍 وضعیت: مجرد\n'
        text+='برای پیشنهاد ازدواج: /marry شناسه_بازیکن\n'
    text+=f"\n👶 فرزندان تحت سرپرستی: {len(children)}\n"
    if children:
        text+='\n'.join(f"👶 {c['name']} | سن: {c['age']} | 😊 {c['happiness']}% | ❤️ {c['health']}%" for c in children)
    text+='\n\nبرای پذیرش فرزند: /adopt نام_کودک'
    await message.answer(text,reply_markup=main_game_kb())

@router.message(Command('marry'))
async def marry(message:Message):
    parts=message.text.split()
    if len(parts)!=2 or not parts[1].isdigit():
        return await message.answer('💍 استفاده: /marry شناسه_بازیکن')
    ok,msg=await create_marriage_proposal(message.from_user.id,int(parts[1]))
    if not ok:
        return await message.answer('❌ '+msg)
    target=await get_user(int(parts[1]))
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='💍 قبول',callback_data=f'marry_accept:{message.from_user.id}'),InlineKeyboardButton(text='❌ رد',callback_data=f'marry_reject:{message.from_user.id}')]])
    try:
        await message.bot.send_message(int(parts[1]), f"💍 {message.from_user.full_name} برای ازدواج با تو پیشنهاد فرستاده است.\n\nبرای تصمیم‌گیری یکی از گزینه‌ها را انتخاب کن.", reply_markup=kb)
        await message.answer('✅ پیشنهاد ازدواج برای بازیکن موردنظر ارسال شد.')
    except Exception:
        await message.answer('⚠️ پیشنهاد ثبت شد، اما نتوانستم پیام مستقیم برای بازیکن بفرستم. او باید قبلاً ربات را شروع کرده باشد.')

async def _respond_marriage(call:CallbackQuery, accept:bool):
    try:
        proposer=int(call.data.split(':')[1])
    except Exception:
        return await call.answer('درخواست نامعتبر است.',show_alert=True)
    async with __import__('aiosqlite').connect('spirits.db') as db:
        cur=await db.execute("SELECT id FROM marriages WHERE user1_id=? AND user2_id=? AND status='pending' ORDER BY id DESC LIMIT 1", (proposer,call.from_user.id))
        row=await cur.fetchone()
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
    parts=message.text.split(maxsplit=1)
    if len(parts)!=2:
        return await message.answer('👶 استفاده: /adopt نام_کودک')
    ok,name=await adopt_child(message.from_user.id,parts[1])
    if not ok:
        return await message.answer('❌ '+name)
    await message.answer(f'👶 سرپرستی {name} با موفقیت ثبت شد.\n\nاز بخش «💍 خانواده» می‌توانی وضعیت کودک را ببینی و از او مراقبت کنی.')

@router.callback_query(F.data=='world:family')
async def family_cb(call:CallbackQuery):
    await family(call.message)
    await call.answer()

@router.message(Command('world'))
@router.message(F.text=='🗺️ جهان')
async def world(message:Message):
    await ensure_user(message.from_user.id,message.from_user.full_name); u=await get_user(message.from_user.id); rows=await list_regions()
    buttons=[]
    for r in rows:
        lock=u['level']<r['unlock_level']; buttons.append([InlineKeyboardButton(text=('🔒 ' if lock else '🗺️ ')+r['name']+f' | سطح {r["unlock_level"]}',callback_data=f'region:{r["id"]}')])
    await message.answer('🗺️ <b>جهان راهنمای ارواح</b>\n\nهر منطقه داستان‌ها و موجودات مخصوص خودش را دارد.',reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith('region:'))
async def region(call:CallbackQuery):
    u=await get_user(call.from_user.id); r=await get_region(int(call.data.split(':')[1]))
    if not r:return await call.answer('منطقه پیدا نشد.',show_alert=True)
    if u['level']<r['unlock_level']:return await call.answer(f'این منطقه از سطح {r["unlock_level"]} باز می‌شود.',show_alert=True)
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='👻 روح‌های منطقه',callback_data=f'rs:{r["id"]}')],[InlineKeyboardButton(text='😈 موجودات منطقه',callback_data=f'rd:{r["id"]}')],[InlineKeyboardButton(text='🗺️ بازگشت',callback_data='world:regions')]])
    await call.message.edit_text(f"🗺️ <b>{r['name']}</b>\n\n{r['description']}",reply_markup=kb); await call.answer()

@router.callback_query(F.data=='world:regions')
async def regions_cb(call:CallbackQuery):
    rows=await list_regions(); u=await get_user(call.from_user.id)
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=('🔒 ' if u['level']<r['unlock_level'] else '🗺️ ')+r['name'],callback_data=f'region:{r["id"]}')] for r in rows])
    await call.message.edit_text('🗺️ <b>جهان</b>',reply_markup=kb); await call.answer()

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
    if u['energy']<=0:return await call.answer('💠 انرژی روحی کافی نداری.',show_alert=True)
    import aiosqlite
    async with aiosqlite.connect('spirits.db') as db:
        await db.execute('UPDATE users SET energy=energy-1 WHERE user_id=?',(call.from_user.id,)); await db.commit()
    correct=opt==c['correct_option']; ok,idx,done=await advance_spirit(call.from_user.id,sid,correct)
    if not correct:
        await call.message.edit_text('🌫️ انتخابت سرنخ را کامل نکرد.\n\nمی‌توانی دوباره بررسی کنی.',reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔎 ادامه بررسی',callback_data=f'clue:{sid}')]])); return await call.answer('سرنخ اشتباه بود.')
    if done:return await complete_spirit(call,sid,s)
    await call.message.edit_text(f'✨ سرنخ پیدا شد!\n\nپیشرفت پرونده: {idx}/{await clue_count(sid)}',reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔎 سرنخ بعدی',callback_data=f'clue:{sid}')]])); await call.answer('درست بود!')

async def clue_count(sid):
    import aiosqlite
    async with aiosqlite.connect('spirits.db') as db:
        cur=await db.execute('SELECT COUNT(*) FROM spirit_clues WHERE spirit_id=?',(sid,)); return (await cur.fetchone())[0]

async def complete_spirit(call,sid,s):
    await add_progress(call.from_user.id,s['reward_coins'],s['reward_xp'],spirit=True)
    import aiosqlite
    async with aiosqlite.connect('spirits.db') as db:
        await db.execute('UPDATE users SET light=light+? WHERE user_id=?',(max(1,s['difficulty']*2),call.from_user.id)); await db.commit()
    await call.message.edit_text(f"✨ <b>روح آرام گرفت</b>\n\n👻 {s['name']} حقیقت را یافت و از مرز میان دو دنیا عبور کرد.\n\n🪙 +{s['reward_coins']} سکه\n✨ +{s['reward_xp']} XP\n✨ +{max(1,s['difficulty']*2)} نور پسین"); await call.answer('روح راهی شد ✨')

@router.callback_query(F.data=='world:spirits')
async def world_spirits(call:CallbackQuery):
    rows=await list_story_spirits(); kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"👻 {s['name']} | ★{s['difficulty']}",callback_data=f'story:{s["id"]}')] for s in rows]); await call.message.edit_text('👻 <b>دفتر ارواح</b>',reply_markup=kb); await call.answer()

@router.callback_query(F.data.startswith('rd:'))
async def region_demons(call:CallbackQuery):
    rid=int(call.data.split(':')[1]); rows=await list_demons(rid); kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"😈 {d['name']} | {'★'*d['rank']}",callback_data=f'demon:{d["id"]}')] for d in rows]+[[InlineKeyboardButton(text='🔙 منطقه',callback_data=f'region:{rid}')]])
    await call.message.edit_text('😈 <b>موجودات منطقه</b>',reply_markup=kb); await call.answer()

@router.message(F.text=='😈 جن‌ها')
async def demons_message(message:Message):
    rows=await list_demons(); kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"😈 {d['name']} | {'★'*d['rank']}",callback_data=f'demon:{d['id']}')] for d in rows]); await message.answer('😈 <b>دفتر موجودات</b>',reply_markup=kb)

@router.callback_query(F.data=='world:demons')
async def demons(call:CallbackQuery):
    rows=await list_demons(); kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"😈 {d['name']} | {'★'*d['rank']}",callback_data=f'demon:{d["id"]}')] for d in rows]); await call.message.edit_text('😈 <b>دفتر موجودات</b>',reply_markup=kb); await call.answer()

@router.callback_query(F.data.startswith('demon:'))
async def demon(call:CallbackQuery):
    did=int(call.data.split(':')[1]); d=await get_demon(did)
    if not d:return await call.answer('موجود پیدا نشد.',show_alert=True)
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔍 بررسی آلودگی',callback_data=f'dcheck:{did}')],[InlineKeyboardButton(text='🔮 مهر محافظ',callback_data=f'dseal:{did}')],[InlineKeyboardButton(text='🕯️ پاک‌سازی',callback_data=f'dclean:{did}')],[InlineKeyboardButton(text='🏃 عقب‌نشینی',callback_data='world:demons')]])
    await call.message.edit_text(f"😈 <b>{d['name']}</b>\n\nنوع: {d['type']}\nرتبه: {'★'*d['rank']}\nمنطقه: {d['region_name']}\n❤️ سلامت: {d['health']}\n☠️ آلودگی: {d['corruption']}٪\n🛡️ دفاع: {d['defense']}\n\n📜 {d['story']}",reply_markup=kb); await call.answer()

@router.callback_query(F.data.startswith('dcheck:'))
async def dcheck(call:CallbackQuery):
    did=int(call.data.split(':')[1]); d=await get_demon(did); e=await get_or_create_encounter(call.from_user.id,did); await call.answer(f"☠️ آلودگی: {e['corruption']}٪ | ❤️ سلامت: {e['health']}",show_alert=True)

@router.callback_query(F.data.startswith('dseal:'))
async def dseal(call:CallbackQuery):
    did=int(call.data.split(':')[1]); d=await get_demon(did); e=await get_or_create_encounter(call.from_user.id,did); u=await get_user(call.from_user.id)
    if u['energy']<2:return await call.answer('💠 انرژی کافی نداری.',show_alert=True)
    import aiosqlite
    async with aiosqlite.connect('spirits.db') as db: await db.execute('UPDATE users SET energy=energy-2 WHERE user_id=?',(call.from_user.id,)); await db.commit()
    corr=max(0,e['corruption']-random.randint(12,24)); hp=max(0,e['health']-random.randint(10,35)); await update_encounter(call.from_user.id,did,hp,corr,e['stage'])
    await call.message.edit_text(f'🔮 مهر محافظ فعال شد!\n\n☠️ آلودگی: {corr}%\n❤️ سلامت: {hp}',reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🕯️ ادامه پاک‌سازی',callback_data=f'dclean:{did}')]])); await call.answer('آلودگی کاهش یافت.')

@router.callback_query(F.data.startswith('dclean:'))
async def dclean(call:CallbackQuery):
    did=int(call.data.split(':')[1]); d=await get_demon(did); e=await get_or_create_encounter(call.from_user.id,did); u=await get_user(call.from_user.id)
    if u['energy']<2:return await call.answer('💠 انرژی کافی نداری.',show_alert=True)
    import aiosqlite
    async with aiosqlite.connect('spirits.db') as db: await db.execute('UPDATE users SET energy=energy-2 WHERE user_id=?',(call.from_user.id,)); await db.commit()
    corr=max(0,e['corruption']-random.randint(15,30)); hp=max(0,e['health']-random.randint(20,55));
    if corr==0:
        await update_encounter(call.from_user.id,did,hp,corr,e['stage'],'completed'); await add_progress(call.from_user.id,d['reward_coins'],d['reward_xp'],cleanse=True)
        await call.message.edit_text(f'✨ <b>پاک‌سازی کامل شد!</b>\n\n😈 {d["name"]} از آلودگی رها شد.\n🪙 +{d["reward_coins"]}\n✨ +{d["reward_xp"]} XP'); return await call.answer('پاک‌سازی کامل شد!')
    await update_encounter(call.from_user.id,did,hp,corr,e['stage']+1)
    await call.message.edit_text(f'🕯️ مرحله پاک‌سازی انجام شد.\n\n☠️ آلودگی باقی‌مانده: {corr}%\n❤️ سلامت موجود: {hp}',reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔮 مهر محافظ',callback_data=f'dseal:{did}'),InlineKeyboardButton(text='🕯️ پاک‌سازی بعدی',callback_data=f'dclean:{did}')]])); await call.answer('ادامه بده!')

@router.message(Command('daily'))
@router.message(F.text=='🎁 جایزه روزانه')
async def daily(message:Message):
    if await daily_claim(message.from_user.id): await message.answer('🎁 پاداش روزانه دریافت شد!\n🪙 +100 سکه\n💠 +5 انرژی')
    else: await message.answer('⏳ پاداش امروز را قبلاً گرفته‌ای.')

@router.message(Command('shop'))
@router.message(F.text=='🛒 فروشگاه')
async def shop(message:Message):
    rows=await list_shop_items(); kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"{r['name']} | 🪙{r['price_coins']} 💎{r['price_gems']}",callback_data=f'shop:{r["id"]}')] for r in rows]); await message.answer('🛒 <b>فروشگاه</b>',reply_markup=kb)

@router.callback_query(F.data.startswith('shop:'))
async def shop_detail(call:CallbackQuery):
    item=await get_shop_item(int(call.data.split(':')[1]));
    if not item:return await call.answer('آیتم پیدا نشد.',show_alert=True)
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🛒 خرید',callback_data=f'buy:{item["id"]}')],[InlineKeyboardButton(text='🔙 فروشگاه',callback_data='shopback')]])
    await call.message.edit_text(f"{item['name']}\n\n{item['description']}\n\n🪙 {item['price_coins']} | 💎 {item['price_gems']}",reply_markup=kb); await call.answer()

@router.callback_query(F.data.startswith('buy:'))
async def buy(call:CallbackQuery):
    ok,res=await buy_shop_item(call.from_user.id,int(call.data.split(':')[1])); await call.answer('خرید انجام شد 🛒' if ok else 'سکه/کریستال کافی نیست.',show_alert=not ok)
    if ok: await call.message.answer(f"✅ {res['name']} به کوله‌پشتی اضافه شد.")

@router.callback_query(F.data=='shopback')
async def shopback(call:CallbackQuery):
    await shop(call.message); await call.answer()

@router.message(Command('inventory'))
@router.message(F.text=='🎒 کوله‌پشتی')
async def inventory(message:Message):
    rows=await get_inventory(message.from_user.id); await message.answer('🎒 <b>کوله‌پشتی</b>\n\n'+(''.join(f"{r['name']} × {r['quantity']}\n" for r in rows) if rows else 'خالی است.'))

@router.callback_query(F.data=='world:inventory')
async def inventory_cb(call:CallbackQuery):
    rows=await get_inventory(call.from_user.id); await call.message.edit_text('🎒 <b>کوله‌پشتی</b>\n\n'+(''.join(f"{r['name']} × {r['quantity']}\n" for r in rows) if rows else 'خالی است.')); await call.answer()

@router.message(Command('rank'))
@router.message(F.text=='🏆 رتبه‌بندی')
async def rank(message:Message):
    rows=await top_users(); await message.answer('🏆 <b>تالار راهنمایان</b>\n\n'+''.join(f"{i}. {r['name']} — سطح {r['level']} | 👻 {r['spirits_sent']} | 😈 {r['cleanses']}\n" for i,r in enumerate(rows,1)))
