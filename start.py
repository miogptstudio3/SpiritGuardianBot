from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import ensure_user, get_user, set_gender

router = Router()

def menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👻 ارواح"), KeyboardButton(text="😈 جن‌ها")],
            [KeyboardButton(text="🗺️ جهان"), KeyboardButton(text="🛡️ پاک‌سازی")],
            [KeyboardButton(text="📜 مأموریت‌ها"), KeyboardButton(text="👤 پروفایل")],
            [KeyboardButton(text="💰 موجودی"), KeyboardButton(text="💰 ارتقای سکه")],
            [KeyboardButton(text="🛒 فروشگاه"), KeyboardButton(text="🎒 کوله‌پشتی")],
            [KeyboardButton(text="🎁 جایزه روزانه"), KeyboardButton(text="🏆 رتبه‌بندی")],
            [KeyboardButton(text="❓ راهنما"), KeyboardButton(text="⚙️ مدیریت")]
        ],
        resize_keyboard=True
    )

WELCOME = """👻 <b>راهنمای محافظ ارواح</b> 🛡️

به مرز میان دو جهان خوش آمدی.

تو یک محافظ و راهنمای ارواح هستی. روح‌های سرگردان را پیدا کن، داستانشان را کشف کن، آخرین خواسته‌شان را انجام بده و آنها را به دنیای پسین راهنمایی کن.

در کنار آن، با موجودات آلوده و جن‌های سرکش روبه‌رو می‌شوی و باید آنها را در قالب مأموریت‌های فانتزی پاک‌سازی کنی.

از منوی پایین شروع کن. 🌑"""

@router.message(CommandStart())
async def start(message: Message):
    await ensure_user(message.from_user.id, message.from_user.full_name)
    user = await get_user(message.from_user.id)
    if not user["gender"]:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="♂️ مرد", callback_data="gender:male"),
            InlineKeyboardButton(text="♀️ زن", callback_data="gender:female")
        ]])
        await message.reply("🧬 <b>انتخاب جنسیت شخصیت</b>\n\nجنسیت شخصیتت را انتخاب کن:", reply_markup=kb)
        return
    await message.reply(WELCOME, reply_markup=menu())

@router.callback_query(F.data.startswith("gender:"))
async def choose_gender(call: CallbackQuery):
    gender = call.data.split(":", 1)[1]
    if gender not in ("male", "female"):
        return await call.answer("انتخاب نامعتبر است.", show_alert=True)
    await ensure_user(call.from_user.id, call.from_user.full_name)
    await set_gender(call.from_user.id, gender)
    label = "مرد ♂️" if gender == "male" else "زن ♀️"
    await call.message.edit_text(f"✅ جنسیت شخصیت ثبت شد: <b>{label}</b>\n\n{WELCOME}")
    await call.message.answer("منوی بازی آماده است. 🎮", reply_markup=menu())
    await call.answer("ثبت شد")

COMMANDS_TEXT = """📋 <b>فهرست دستورات ربات</b>

<b>🎮 بازی و منو</b>
/start — شروع و منوی اصلی
/help یا /commands — همین راهنما
/profile — پروفایل شخصیت
/balance — موجودی سکه و انرژی
/daily — جایزه روزانه (+ کریستال)
/missions — مأموریت‌های روزانه کریستال
/shop — فروشگاه
/inventory — کوله‌پشتی
/rank — رتبه‌بندی
/upgrade_coins — ارتقای پاداش سکه
/mind یا پرورش ذهن — تمرین قدرت ذهن
/stats — آمار قدرت‌ها
/world — جهان و مناطق
/spirits یا ارواح — دفتر ارواح
/family — خانواده
/marry آیدی — پیشنهاد ازدواج
/adopt نام — سرپرستی کودک

<b>📌 دکمه‌های منو</b>
👻 ارواح | 😈 جن‌ها | 🗺️ جهان | 🛡️ پاک‌سازی
📜 مأموریت‌ها | 👤 پروفایل | 💰 موجودی | 💰 ارتقای سکه
🛒 فروشگاه | 🎒 کوله‌پشتی | 🎁 جایزه روزانه | 🏆 رتبه‌بندی
❓ راهنما | ⚙️ مدیریت

<b>⚙️ دستورات مدیریتی</b> (نیاز به رتبه)
/panel — پنل مدیریت
/usersearch نام یا ID
/give ID سکه انرژی
/setgems ID مقدار
/sethealth ID مقدار
/setlevel ID سطح
/warn ID دلیل
/tempban ID دقیقه دلیل
/ban ID [دلیل]
/unban ID
/setrole ID رتبه  یا  /addstaff ID رتبه
/removestaff ID
/adminlogs
/addspirit نام|توضیح|خواسته|سختی|سکه|XP
/addshop نام|توضیح|دسته|سکه|کریستال|انرژی|بونوس
/broadcast متن

هرچه مأموریت بیشتری انجام بدهی، سطح و پاداش‌هایت بیشتر می‌شود.
با ارتقای سکه می‌توانی پاداش مأموریت‌ها را تا +۵۰٪ قوی‌تر کنی."""


@router.message(Command("help"))
@router.message(Command("commands"))
@router.message(F.text == "❓ راهنما")
async def help_cmd(message: Message):
    await message.reply(COMMANDS_TEXT)
