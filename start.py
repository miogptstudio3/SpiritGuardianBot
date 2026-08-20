from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from database import ensure_user

router = Router()

def menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👻 ارواح"), KeyboardButton(text="😈 جن‌ها")],
            [KeyboardButton(text="🗺️ جهان"), KeyboardButton(text="🛡️ پاک‌سازی")],
            [KeyboardButton(text="📜 مأموریت‌ها"), KeyboardButton(text="👤 پروفایل")],
            [KeyboardButton(text="💰 موجودی"), KeyboardButton(text="🛒 فروشگاه")],
            [KeyboardButton(text="🎒 کوله‌پشتی"), KeyboardButton(text="🎁 جایزه روزانه")],
            [KeyboardButton(text="🏆 رتبه‌بندی"), KeyboardButton(text="❓ راهنما")],
            [KeyboardButton(text="⚙️ مدیریت")]
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
    await message.answer(WELCOME, reply_markup=menu())

@router.message(Command("help"))
@router.message(F.text == "❓ راهنما")
async def help_cmd(message: Message):
    await message.answer(
        "📖 <b>راهنما</b>\n\n"
        "👻 ارواح — فهرست روح‌های فعال\n"
        "😈 جن‌ها — موجودات و پرونده‌های پاک‌سازی\n"
        "🛡️ پاک‌سازی — عملیات پاک‌سازی فانتزی\n"
        "📜 مأموریت‌ها — مأموریت‌های در دسترس\n"
        "👤 پروفایل — وضعیت شخصیت\n"
        "💰 موجودی — سکه و انرژی\n"
        "🎁 جایزه روزانه — دریافت پاداش روزانه\n"
        "🏆 رتبه‌بندی — برترین محافظان\n\n"
        "هرچه مأموریت بیشتری انجام بدهی، سطح و پاداش‌هایت بیشتر می‌شود."
    )
