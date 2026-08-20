import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from database import init_db, is_banned
from start import router as start_router
from game import router as game_router
from admin import router as admin_router


def register_handlers(dp):
    dp.include_router(start_router)
    dp.include_router(game_router)
    dp.include_router(admin_router)


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


async def health(request):
    return web.Response(text="OK - Spirit Guide Bot is alive", status=200)


async def health_server():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    app.router.add_get("/healthz", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Health server listening on 0.0.0.0:{port}")
    return runner


async def main():
    await init_db()
    runner = await health_server()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    register_handlers(dp)
    dp.message.middleware(BanMiddleware())
    dp.callback_query.middleware(BanMiddleware())
    print("👻 راهنمای محافظ ارواح فعال شد.")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
