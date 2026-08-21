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

@router.message(Command("help"))
@router.message(F.text == "❓ راهنما")
async def help_cmd(message: Message):
    await message.reply(
        "📖 <b>راهنما</b>\n\n"
        "👻 ارواح — فهرست روح‌های فعال\n"
        "😈 جن‌ها — موجودات و پرونده‌های پاک‌سازی\n"
        "🛡️ پاک‌سازی — عملیات پاک‌سازی فانتزی\n"
        "📜 مأموریت‌ها — مأموریت‌های در دسترس\n"
        "👤 پروفایل — وضعیت شخصیت\n"
        "💰 موجودی — سکه و انرژی\n"
        "💰 ارتقای سکه — افزایش درصد پاداش سکه از مأموریت‌ها (تا +۵۰٪)\n"
        "🎁 جایزه روزانه — دریافت پاداش روزانه\n"
        "🏆 رتبه‌بندی — برترین محافظان\n\n"
        "هرچه مأموریت بیشتری انجام بدهی، سطح و پاداش‌هایت بیشتر می‌شود.\n"
        "با ارتقای سکه می‌توانی پاداش مأموریت‌ها را قوی‌تر کنی."
    )
