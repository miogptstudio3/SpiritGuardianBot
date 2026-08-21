from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import ROLE_LEVELS, ROLE_PERMISSIONS, CREATOR_ID
from database import (
    get_role, set_role, remove_staff, set_ban, clear_ban,
    get_user_count, get_spirit_count, get_staff_list, admin_give,
    list_shop_items, search_users, get_full_user, admin_update_user,
    add_warning, get_warnings, set_temporary_ban, add_admin_log,
    get_admin_logs, get_inventory_for_admin, add_spirit, admin_add_shop_item,
    ensure_user, get_user
)

router=Router()

def can(role, p):
    # ویژه و سازنده اصلی همیشه همه دسترسی‌ها را دارند
    if role == "ویژه":
        return True
    return p in ROLE_PERMISSIONS.get(role, set())

async def deny(event):
    text = "⛔ دسترسی کافی نداری."
    from aiogram.types import CallbackQuery
    try:
        if isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
        else:
            await event.reply(text)
    except Exception:
        pass

async def require_perm(event, perm):
    role = await get_role(event.from_user.id)
    if not can(role, perm):
        await deny(event)
        return None
    return role

async def can_manage_target(actor_id, target_id):
    if target_id == CREATOR_ID:
        return False
    actor_role = await get_role(actor_id)
    target_role = await get_role(target_id)
    return ROLE_LEVELS.get(actor_role, 0) > ROLE_LEVELS.get(target_role, 0)

def back():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 پنل مدیریت",callback_data="adm:home")]
    ])

def user_buttons(rows):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"👤 {r['name'][:25]} | {r['user_id']}",
                              callback_data=f"usr:{r['user_id']}")]
        for r in rows
    ]+[ [InlineKeyboardButton(text="🔙 پنل مدیریت",callback_data="adm:home")] ])

def user_panel(uid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 پروفایل",callback_data=f"upro:{uid}"),
         InlineKeyboardButton(text="🎒 موجودی",callback_data=f"uinv:{uid}")],
        [InlineKeyboardButton(text="💰 منابع",callback_data=f"uedit:{uid}:resources"),
         InlineKeyboardButton(text="❤️ سلامتی",callback_data=f"uedit:{uid}:health")],
        [InlineKeyboardButton(text="⭐ سطح",callback_data=f"uedit:{uid}:level"),
         InlineKeyboardButton(text="⚠️ اخطار",callback_data=f"uwarn:{uid}")],
        [InlineKeyboardButton(text="🚫 بن موقت",callback_data=f"uban:{uid}:temp"),
         InlineKeyboardButton(text="♻️ رفع بن",callback_data=f"uban:{uid}:clear")],
        [InlineKeyboardButton(text="🔙 کاربران",callback_data="adm:users")]
    ])

@router.message(Command("panel"))
@router.message(F.text=="⚙️ مدیریت")
async def panel(message:Message):
    role=await get_role(message.from_user.id)
    if not can(role,"panel"): return await deny(message)
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 آمار",callback_data="adm:stats"),
         InlineKeyboardButton(text="👥 کاربران",callback_data="adm:users")],
        [InlineKeyboardButton(text="👑 تیم مدیریت",callback_data="adm:staff"),
         InlineKeyboardButton(text="📜 لاگ مدیران",callback_data="adm:logs")],
        [InlineKeyboardButton(text="👻 ارواح",callback_data="adm:spirits"),
         InlineKeyboardButton(text="🛒 فروشگاه",callback_data="adm:shop")],
        [InlineKeyboardButton(text="👑 رتبه‌ها",callback_data="adm:roles"),
         InlineKeyboardButton(text="📖 راهنما",callback_data="adm:help")]
    ])
    await message.reply(f"⚙️ <b>پنل مدیریت</b>\n\n👑 رتبه: <b>{role}</b>\nاز منو انتخاب کن:",reply_markup=kb)

@router.callback_query(F.data.startswith("adm:"))
async def adm(call:CallbackQuery):
    role=await get_role(call.from_user.id); a=call.data.split(":")[1]
    perms={"stats":"stats","users":"users","staff":"users","logs":"logs","spirits":"addspirit","shop":"shop","roles":"setrole","help":"panel"}
    required = perms.get(a, "panel" if a == "home" else None)
    if required and not can(role, required): return await deny(call)
    if a=="home":
        await call.message.edit_text("⚙️ <b>پنل مدیریت</b>\n\nیک بخش را انتخاب کن:",reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 آمار",callback_data="adm:stats"),InlineKeyboardButton(text="👥 کاربران",callback_data="adm:users")],
            [InlineKeyboardButton(text="👑 تیم مدیریت",callback_data="adm:staff"),InlineKeyboardButton(text="📜 لاگ مدیران",callback_data="adm:logs")],
            [InlineKeyboardButton(text="👻 ارواح",callback_data="adm:spirits"),InlineKeyboardButton(text="🛒 فروشگاه",callback_data="adm:shop")],
            [InlineKeyboardButton(text="👑 رتبه‌ها",callback_data="adm:roles"),InlineKeyboardButton(text="📖 راهنما",callback_data="adm:help")]
        ]))
    elif a=="stats":
        await call.message.edit_text(f"📊 <b>آمار</b>\n\n👤 کاربران: {await get_user_count()}\n👻 ارواح فعال: {await get_spirit_count()}",reply_markup=back())
    elif a=="users":
        await call.message.edit_text("👥 <b>مدیریت کاربران</b>\n\nجستجو با دستور:\n<code>/usersearch نام یا ID</code>\n\nیا مستقیماً ID را جستجو کن.",reply_markup=back())
    elif a=="staff":
        rows=await get_staff_list(); t="👑 <b>تیم مدیریت</b>\n\n"+("".join(f"• <code>{x['user_id']}</code> — {x['role']}\n" for x in rows) or "خالی")
        await call.message.edit_text(t,reply_markup=back())
    elif a=="logs":
        rows=await get_admin_logs()
        t="📜 <b>لاگ فعالیت مدیران</b>\n\n"
        t+="".join(f"• {x['created_at']} | <code>{x['admin_id']}</code> | {x['action']} | {x['target_id'] or '-'}\n" for x in rows) or "لاگی ثبت نشده."
        await call.message.edit_text(t[:4000],reply_markup=back())
    elif a=="spirits":
        await call.message.edit_text("👻 مدیریت ارواح\n\nافزودن: /addspirit نام|توضیح|خواسته|سختی|سکه|XP",reply_markup=back())
    elif a=="shop":
        items=await list_shop_items()
        t="🛒 <b>فروشگاه</b>\n\n"+"".join(f"#{x['id']} {x['name']} — 🪙{x['price_coins']} 💎{x['price_gems']}\n" for x in items[:30])
        await call.message.edit_text(t+"\n/addshop نام|توضیح|دسته|سکه|کریستال|انرژی|بونوس",reply_markup=back())
    elif a=="roles":
        await call.message.edit_text("👑 ویژه\n👑 مدیر\n🛡️ معاون مدیر\n🔰 معاون ادمین\n⚙️ ادمین\n🧩 معاون سازنده\n🔨 سازنده",reply_markup=back())
    elif a=="help":
        await call.message.edit_text("📖 مدیریت کاربران: /usersearch نام یا ID\nتغییر منابع و سلامت و سطح از صفحه کاربر انجام می‌شود.\nهمه تغییرات مدیریتی در لاگ ثبت می‌شوند.",reply_markup=back())
    await call.answer()

@router.message(Command("usersearch"))
async def usersearch(message:Message):
    role=await get_role(message.from_user.id)
    if not can(role,"users"): return await deny(message)
    term=message.text.partition(" ")[2].strip()
    if not term: return await message.reply("فرمت: /usersearch نام یا ID")
    rows=await search_users(term)
    if not rows: return await message.reply("🔎 کاربری پیدا نشد.")
    await message.reply("🔎 <b>نتایج جستجو</b>\n\nکاربر را انتخاب کن:",reply_markup=user_buttons(rows))

@router.callback_query(F.data.startswith("usr:"))
async def user_page(call:CallbackQuery):
    role=await get_role(call.from_user.id)
    if not can(role,"users"): return await deny(call)
    uid=int(call.data.split(":")[1])
    if uid == CREATOR_ID:
        return await call.answer('🔒 حساب سازنده قابل مدیریت نیست.', show_alert=True)
    user,mod,wc=await get_full_user(uid)
    if not user: return await call.answer("کاربر پیدا نشد.",show_alert=True)
    ban="🚫 مسدود" if mod and mod["banned"] else "✅ آزاد"
    await call.message.edit_text(f"👤 <b>{user['name']}</b>\nID: <code>{uid}</code>\nوضعیت: {ban}\n⚠️ اخطار: {wc}\n\nاز منو انتخاب کن:",reply_markup=user_panel(uid))
    await call.answer()

@router.callback_query(F.data.startswith("upro:"))
async def user_profile(call:CallbackQuery):
    role=await get_role(call.from_user.id)
    if not can(role,"users"): return await deny(call)
    uid=int(call.data.split(":")[1]);
    if uid == CREATOR_ID:
        return await call.answer('🔒 حساب سازنده قابل مدیریت نیست.', show_alert=True)
    u,m,w=await get_full_user(uid)
    if not u: return await call.answer("کاربر پیدا نشد.",show_alert=True)
    await call.message.edit_text(
        f"📋 <b>پروفایل مدیریتی</b>\n\n👤 {u['name']}\n🆔 <code>{uid}</code>\n"
        f"⭐ سطح: {u['level']}\n✨ XP: {u['xp']}\n❤️ سلامتی: {u['health']}/{u['max_health']}\n"
        f"🔋 انرژی: {u['energy']}\n🪙 سکه: {u['coins']}\n💎 کریستال: {u['soul_gems']}\n"
        f"👻 ارواح: {u['spirits_sent']}\n🛡️ پاک‌سازی: {u['cleanses']}\n⚠️ اخطار: {w}",
        reply_markup=user_panel(uid))
    await call.answer()

@router.callback_query(F.data.startswith("uinv:"))
async def user_inv(call:CallbackQuery):
    role=await get_role(call.from_user.id)
    if not can(role,"users"): return await deny(call)
    uid=int(call.data.split(":")[1]); rows=await get_inventory_for_admin(uid)
    t="🎒 <b>موجودی کاربر</b>\n\n"+("".join(f"{x['name']} × {x['quantity']}\n" for x in rows) or "کوله‌پشتی خالی است.")
    await call.message.edit_text(t,reply_markup=user_panel(uid))
    await call.answer()

@router.callback_query(F.data.startswith("uedit:"))
async def edit_help(call:CallbackQuery):
    role=await get_role(call.from_user.id)
    if not can(role,"give"): return await deny(call)
    _,uid,kind=call.data.split(":")
    texts={
        "resources":f"💰 منابع کاربر <code>{uid}</code>\n\n/give {uid} coins energy\nبرای کریستال: /setgems {uid} مقدار\n",
        "health":f"❤️ سلامتی <code>{uid}</code>\n\n/sethealth {uid} مقدار\nمثال: /sethealth {uid} 100",
        "level":f"⭐ سطح <code>{uid}</code>\n\n/setlevel {uid} سطح\nمثال: /setlevel {uid} 10"
    }
    await call.message.edit_text(texts[kind],reply_markup=user_panel(int(uid)))
    await call.answer()

@router.callback_query(F.data.startswith("uwarn:"))
async def warn_help(call:CallbackQuery):
    role=await get_role(call.from_user.id)
    if not can(role,"ban"): return await deny(call)
    uid=int(call.data.split(":")[1])
    await call.message.edit_text(f"⚠️ اخطار به <code>{uid}</code>\n\n/warn {uid} دلیل اخطار",reply_markup=user_panel(uid))
    await call.answer()

@router.callback_query(F.data.startswith("uban:"))
async def ban_help(call:CallbackQuery):
    role=await get_role(call.from_user.id)
    if not can(role,"ban"): return await deny(call)
    _,uid,kind=call.data.split(":")
    uid=int(uid)
    if kind=="clear":
        if not await can_manage_target(call.from_user.id, uid):
            return await call.answer("⛔ نمی‌توانی کاربری هم‌سطح یا بالاتر را مدیریت کنی.", show_alert=True)
        await clear_ban(uid); await add_admin_log(call.from_user.id,"رفع بن",uid,"از پنل")
        await call.message.edit_text("♻️ بن کاربر برداشته شد.",reply_markup=user_panel(uid))
    else:
        if not await can_manage_target(call.from_user.id, uid):
            return await call.answer("⛔ نمی‌توانی کاربری هم‌سطح یا بالاتر را مدیریت کنی.", show_alert=True)
        await call.message.edit_text(f"🚫 بن موقت <code>{uid}</code>\n\n/tempban {uid} دقیقه دلیل",reply_markup=user_panel(uid))
    await call.answer()

# Direct management commands.
@router.message(Command("setgems"))
async def setgems(message:Message):
    role=await get_role(message.from_user.id)
    if not can(role,"setgems") and not can(role,"give"): return await deny(message)
    p=message.text.split()
    if len(p)!=3 or not p[1].isdigit() or not p[2].lstrip("-").isdigit(): return await message.reply("فرمت: /setgems ID مقدار")
    uid,delta=int(p[1]),int(p[2])
    if not await can_manage_target(message.from_user.id, uid): return await message.reply("⛔ نمی‌توانی کاربری هم‌سطح یا بالاتر را تغییر بدهی.")
    await admin_update_user(uid,gems=delta); await add_admin_log(message.from_user.id,"تغییر کریستال",uid,str(delta))
    await message.reply("💎 کریستال تغییر کرد.")

@router.message(Command("sethealth"))
async def sethealth(message:Message):
    role=await get_role(message.from_user.id)
    if not can(role,"sethealth") and not can(role,"give"): return await deny(message)
    p=message.text.split()
    if len(p)!=3 or not p[1].isdigit() or not p[2].isdigit(): return await message.reply("فرمت: /sethealth ID مقدار")
    uid,h=int(p[1]),int(p[2])
    if not await can_manage_target(message.from_user.id, uid): return await message.reply("⛔ نمی‌توانی کاربری هم‌سطح یا بالاتر را تغییر بدهی.")
    await admin_update_user(uid,health=h); await add_admin_log(message.from_user.id,"تغییر سلامت",uid,str(h))
    await message.reply("❤️ سلامتی تغییر کرد.")

@router.message(Command("setlevel"))
async def setlevel(message:Message):
    role=await get_role(message.from_user.id)
    if not can(role,"setlevel") and not can(role,"setrole"): return await deny(message)
    p=message.text.split()
    if len(p)!=3 or not p[1].isdigit() or not p[2].isdigit(): return await message.reply("فرمت: /setlevel ID سطح")
    uid,l=int(p[1]),int(p[2])
    if not await can_manage_target(message.from_user.id, uid): return await message.reply("⛔ نمی‌توانی کاربری هم‌سطح یا بالاتر را تغییر بدهی.")
    await admin_update_user(uid,level=l); await add_admin_log(message.from_user.id,"تغییر سطح",uid,str(l))
    await message.reply("⭐ سطح تغییر کرد.")

@router.message(Command("warn"))
async def warn(message:Message):
    role=await get_role(message.from_user.id)
    if not can(role,"ban"): return await deny(message)
    p=message.text.split(maxsplit=2)
    if len(p)<3 or not p[1].isdigit(): return await message.reply("فرمت: /warn ID دلیل")
    uid,reason=int(p[1]),p[2]
    if not await can_manage_target(message.from_user.id, uid): return await message.reply("⛔ نمی‌توانی کاربری هم‌سطح یا بالاتر را مدیریت کنی.")
    await add_warning(uid,message.from_user.id,reason); await add_admin_log(message.from_user.id,"اخطار",uid,reason)
    await message.reply("⚠️ اخطار ثبت شد.")

@router.message(Command("tempban"))
async def tempban(message:Message):
    role=await get_role(message.from_user.id)
    if not can(role,"ban"): return await deny(message)
    p=message.text.split(maxsplit=2)
    if len(p)<3 or not p[1].isdigit() or not p[2].split()[0].isdigit(): return await message.reply("فرمت: /tempban ID دقیقه دلیل")
    uid=int(p[1]); mins=int(p[2].split()[0]); reason=" ".join(p[2].split()[1:]) or "بدون دلیل"
    target_role=await get_role(uid)
    if ROLE_LEVELS[target_role]>=ROLE_LEVELS[role]: return await message.reply("⛔ این کاربر رتبه هم‌سطح یا بالاتر دارد.")
    until=(datetime.now(timezone.utc)+timedelta(minutes=mins)).isoformat()
    await set_temporary_ban(uid,until,reason); await add_admin_log(message.from_user.id,"بن موقت",uid,f"{mins} دقیقه: {reason}")
    await message.reply(f"🚫 کاربر به مدت {mins} دقیقه بن شد.")

@router.message(Command("adminlogs"))
async def adminlogs(message:Message):
    role=await get_role(message.from_user.id)
    if not can(role,"logs") and not can(role,"users"): return await deny(message)
    rows=await get_admin_logs()
    t="📜 <b>لاگ مدیران</b>\n\n"+"".join(f"{x['created_at']} | {x['admin_id']} | {x['action']} | {x['target_id'] or '-'} | {x['details'] or ''}\n" for x in rows)
    await message.reply(t[:4000] or "لاگ خالی است.")


# ——— دستورات اختصاصی سازنده / ویژه ———

VALID_ROLES = [r for r in ROLE_LEVELS.keys() if r != "کاربر"]

@router.message(Command("addstaff"))
@router.message(Command("setrole"))
async def addstaff(message: Message):
    """افزودن یا تغییر رتبه عضو تیم مدیریت با آیدی عددی.
    فقط ویژه/سازنده اصلی.
    فرمت: /addstaff ID رتبه
    مثال: /addstaff 123456789 ادمین
    """
    role = await get_role(message.from_user.id)
    if role != "ویژه" and message.from_user.id != CREATOR_ID:
        return await deny(message)
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3 or not parts[1].lstrip("-").isdigit():
        roles_list = " | ".join(VALID_ROLES)
        return await message.reply(
            "فرمت:\n<code>/addstaff آیدی_عددی رتبه</code>\n\n"
            f"رتبه‌های مجاز:\n{roles_list}\n\n"
            "مثال:\n<code>/addstaff 123456789 ادمین</code>"
        )
    uid = int(parts[1])
    new_role = parts[2].strip()
    if new_role not in ROLE_LEVELS or new_role == "کاربر":
        return await message.reply("⛔ رتبه نامعتبر است. رتبه‌های مجاز: " + " | ".join(VALID_ROLES))
    if uid == CREATOR_ID:
        return await message.reply("🔒 حساب سازنده اصلی قابل تغییر نیست.")
    # ویژه می‌تواند هر رتبه‌ای بدهد؛ بقیه فقط پایین‌تر از خودشان
    actor_level = ROLE_LEVELS.get(role, 0)
    target_level = ROLE_LEVELS.get(new_role, 0)
    if role != "ویژه" and target_level >= actor_level:
        return await message.reply("⛔ نمی‌توانی رتبه هم‌سطح یا بالاتر از خودت بدهی.")
    await set_role(uid, new_role)
    await add_admin_log(message.from_user.id, "افزودن/تغییر رتبه", uid, new_role)
    await message.reply(
        f"✅ کاربر <code>{uid}</code> با رتبه <b>{new_role}</b> به تیم مدیریت اضافه/به‌روز شد."
    )


@router.message(Command("removestaff"))
async def removestaff_cmd(message: Message):
    """حذف از تیم مدیریت. فقط ویژه."""
    role = await get_role(message.from_user.id)
    if role != "ویژه" and message.from_user.id != CREATOR_ID:
        return await deny(message)
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].lstrip("-").isdigit():
        return await message.reply("فرمت: <code>/removestaff آیدی_عددی</code>")
    uid = int(parts[1])
    if uid == CREATOR_ID:
        return await message.reply("🔒 حساب سازنده اصلی قابل حذف نیست.")
    await remove_staff(uid)
    await add_admin_log(message.from_user.id, "حذف از تیم مدیریت", uid, "")
    await message.reply(f"♻️ کاربر <code>{uid}</code> از تیم مدیریت حذف شد.")


@router.message(Command("give"))
async def give_cmd(message: Message):
    """فرمت: /give ID سکه انرژی"""
    role = await require_perm(message, "give")
    if role is None:
        return
    parts = message.text.split()
    if len(parts) < 3 or not parts[1].lstrip("-").isdigit():
        return await message.reply("فرمت: <code>/give آیدی سکه انرژی</code>\nمثال: /give 123456 100 5")
    uid = int(parts[1])
    if not await can_manage_target(message.from_user.id, uid):
        return await message.reply("⛔ نمی‌توانی این کاربر را مدیریت کنی.")
    try:
        coins = int(parts[2]) if len(parts) > 2 else 0
        energy = int(parts[3]) if len(parts) > 3 else 0
    except ValueError:
        return await message.reply("مقادیر سکه و انرژی باید عدد باشند.")
    await ensure_user(uid, f"User{uid}")
    await admin_give(uid, coins, energy)
    await add_admin_log(message.from_user.id, "give", uid, f"coins={coins} energy={energy}")
    await message.reply(f"✅ به کاربر <code>{uid}</code> داده شد:\n🪙 {coins} سکه\n💠 {energy} انرژی")


@router.message(Command("ban"))
async def ban_cmd(message: Message):
    """فرمت: /ban ID [دلیل]"""
    role = await require_perm(message, "ban")
    if role is None:
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        return await message.reply("فرمت: <code>/ban آیدی [دلیل]</code>")
    uid = int(parts[1])
    if not await can_manage_target(message.from_user.id, uid):
        return await message.reply("⛔ نمی‌توانی این کاربر را مدیریت کنی.")
    if uid == CREATOR_ID:
        return await message.reply("🔒 حساب سازنده اصلی قابل مسدودسازی نیست.")
    reason = parts[2] if len(parts) > 2 else "بدون دلیل"
    await set_ban(uid, True)
    await add_admin_log(message.from_user.id, "ban", uid, reason)
    await message.reply(f"🚫 کاربر <code>{uid}</code> مسدود شد.\nدلیل: {reason}")


@router.message(Command("unban"))
async def unban_cmd(message: Message):
    """فرمت: /unban ID"""
    role = await require_perm(message, "ban")
    if role is None:
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].lstrip("-").isdigit():
        return await message.reply("فرمت: <code>/unban آیدی</code>")
    uid = int(parts[1])
    await clear_ban(uid)
    await add_admin_log(message.from_user.id, "unban", uid, "")
    await message.reply(f"✅ مسدودیت کاربر <code>{uid}</code> برداشته شد.")


@router.message(Command("addspirit"))
async def addspirit_cmd(message: Message):
    """فرمت: /addspirit نام|توضیح|خواسته|سختی|سکه|XP"""
    role = await require_perm(message, "addspirit")
    if role is None:
        return
    raw = message.text.partition(" ")[2].strip()
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 6:
        return await message.reply(
            "فرمت:\n<code>/addspirit نام|توضیح|خواسته|سختی|سکه|XP</code>\n"
            "مثال: /addspirit روح گمشده|یک روح سرگردان|یافتن فرزندش|2|80|40"
        )
    try:
        name, desc, request, diff, coins, xp = parts[0], parts[1], parts[2], int(parts[3]), int(parts[4]), int(parts[5])
    except ValueError:
        return await message.reply("سختی، سکه و XP باید عدد باشند.")
    sid = await add_spirit(name, desc, request, diff, coins, xp)
    await add_admin_log(message.from_user.id, "addspirit", None, f"{name} (id={sid})")
    await message.reply(f"✅ روح جدید اضافه شد.\nID: <code>{sid}</code>\nنام: {name}")


@router.message(Command("addshop"))
async def addshop_cmd(message: Message):
    """فرمت: /addshop نام|توضیح|دسته|سکه|کریستال|انرژی|بونوس"""
    role = await require_perm(message, "shop")
    if role is None:
        return
    raw = message.text.partition(" ")[2].strip()
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 7:
        return await message.reply(
            "فرمت:\n<code>/addshop نام|توضیح|دسته|سکه|کریستال|انرژی|بونوس</code>\n"
            "مثال: /addshop چای جدید|بازیابی انرژی|🍵 خوراکی|40|0|4|0"
        )
    try:
        name, desc, cat = parts[0], parts[1], parts[2]
        coins, gems, energy, bonus = int(parts[3]), int(parts[4]), int(parts[5]), int(parts[6])
    except ValueError:
        return await message.reply("مقادیر عددی (سکه، کریستال، انرژی، بونوس) باید عدد باشند.")
    sid = await admin_add_shop_item(name, desc, cat, coins, gems, energy, bonus)
    await add_admin_log(message.from_user.id, "addshop", None, f"{name} (id={sid})")
    await message.reply(f"✅ آیتم فروشگاه اضافه شد.\nID: <code>{sid}</code>\nنام: {name}")


@router.message(Command("broadcast"))
async def broadcast_cmd(message: Message):
    """فرمت: /broadcast متن پیام"""
    role = await require_perm(message, "broadcast")
    if role is None:
        return
    text = message.text.partition(" ")[2].strip()
    if not text:
        return await message.reply("فرمت: <code>/broadcast متن پیام</code>")
    # برای سادگی فقط تأیید می‌کنیم؛ ارسال واقعی به همه کاربران می‌تواند سنگین باشد
    # در نسخه کامل می‌توان از صف استفاده کرد.
    await add_admin_log(message.from_user.id, "broadcast", None, text[:200])
    await message.reply(
        f"📢 پیام برای پخش آماده شد (لاگ ثبت شد):\n\n{text}\n\n"
        "⚠️ ارسال انبوه به همه کاربران فعلاً برای جلوگیری از محدودیت تلگرام غیرفعال است. "
        "در صورت نیاز از پنل یا اسکریپت جداگانه استفاده کنید."
    )
