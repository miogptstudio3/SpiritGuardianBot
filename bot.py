import asyncio
from aiogram import Bot, Dispatcher
from aiogram import BaseMiddleware
from database import is_banned
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from database import init_db
from handlers import register_handlers


class BanMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user and await is_banned(user.id):
            try:
                await event.answer("🚫 دسترسی شما به ربات مسدود شده است.")
            except Exception:
                pass
            return
        return await handler(event, data)

async def main():
    await init_db()
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    register_handlers(dp)
    dp.message.middleware(BanMiddleware())
    dp.callback_query.middleware(BanMiddleware())
    print("👻 راهنمای محافظ ارواح فعال شد.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
