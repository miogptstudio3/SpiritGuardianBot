"""
نقطه ورود واحد: ربات تلگرام (Polling) + Web App روی یک پورت.
روی Render فقط یک Web Service با Start Command: python bot.py کافی است.
"""
import asyncio
import logging
import os
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent

from config import BOT_TOKEN
from database import init_db, is_banned
from start import router as start_router
from game import router as game_router
from admin import router as admin_router

# Web App کامل (صفحه + API) — همان app ساخته‌شده در web_app.py
from web_app import app as webapp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("spirit-bot")


def register_handlers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(game_router)
    dp.include_router(admin_router)


class BanMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user and await is_banned(user.id):
            try:
                if hasattr(event, "answer"):
                    await event.answer("🚫 دسترسی شما به ربات مسدود شده است.")
            except Exception:
                pass
            return
        return await handler(event, data)


async def on_error(event: ErrorEvent):
    logger.exception(
        "Unhandled error while processing update: %s",
        event.exception,
        exc_info=event.exception,
    )
    try:
        if event.update.callback_query:
            await event.update.callback_query.answer(
                "⚠️ خطایی رخ داد. لطفاً دوباره تلاش کن.", show_alert=True
            )
        elif event.update.message:
            await event.update.message.reply(
                "⚠️ مشکلی پیش آمد. چند ثانیه صبر کن و دوباره امتحان کن."
            )
    except Exception:
        pass


async def start_web_server():
    """راه‌اندازی Web App + Health روی PORT (همان پورتی که Render می‌دهد)."""
    # اطمینان از مسیرهای health برای Render
    try:
        webapp.router.add_get("/healthz", lambda r: web.Response(text="OK", status=200))
    except Exception:
        pass  # ممکن است قبلاً اضافه شده باشد

    runner = web.AppRunner(webapp)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("🌐 Web App + API listening on 0.0.0.0:%s", port)
    logger.info("   URL این سرویس را در BotFather به‌عنوان Web App بگذار.")
    return runner


async def run_bot():
    await init_db()
    runner = await start_web_server()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    register_handlers(dp)
    dp.message.middleware(BanMiddleware())
    dp.callback_query.middleware(BanMiddleware())
    dp.errors.register(on_error)

    logger.info("👻 راهنمای محافظ ارواح فعال شد (ربات + وب‌اپ یکجا).")
    backoff = 1
    try:
        while True:
            try:
                await dp.start_polling(bot, handle_signals=False)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(
                    "Polling stopped with error: %s — restarting in %ss", e, backoff
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)
            else:
                await asyncio.sleep(3)
                backoff = 1
    finally:
        await bot.session.close()
        await runner.cleanup()
        logger.info("Bot shut down cleanly.")


async def main():
    await run_bot()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
