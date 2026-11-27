import asyncio
import logging
import ssl
import sys
from contextlib import suppress

import aiohttp
import ccxt.async_support as ccxt
import certifi
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from core.commands import set_commands
from core.config import TELEGRAM_BOT_TOKEN
from core.context import AppContext
from core.database import init_db
from core.middlewares import UserAndThrottleMiddleware
from core.redis_client import cache
from handlers import start, alerts, price, funding, top, charts, currencies
from services.api_helpers import refresh_markets_task

try:
    import uvloop
    LOOP_FACTORY = uvloop.new_event_loop
except ImportError:
    LOOP_FACTORY = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def start_bot():
    """Configures and launches the Telegram bot with shared AppContext and background workers."""
    init_db()

    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Register global middleware for throttling, language detection, and anonymous user filtering
    middleware = UserAndThrottleMiddleware(rate_limit=0.6)
    dp.message.middleware(middleware)
    dp.callback_query.middleware(middleware)

    dp.include_router(start.router)
    dp.include_router(alerts.router)
    dp.include_router(funding.router)
    dp.include_router(top.router)
    dp.include_router(charts.router)
    dp.include_router(currencies.router)
    dp.include_router(price.router)

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    timeout = aiohttp.ClientTimeout(total=10)
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    http_session = aiohttp.ClientSession(connector=connector, timeout=timeout)
    exchange = ccxt.binance()

    ctx = AppContext(exchange=exchange, markets={}, http_session=http_session)
    dp["ctx"] = ctx

    alerts_task = None
    markets_task = None

    try:
        await set_commands(bot)
        await exchange.load_markets()
        ctx.markets.update(exchange.markets)
        logging.info(f"Market data loaded from Binance ({len(ctx.markets)} symbols).")

        alerts_task = asyncio.create_task(alerts.check_alerts_task(bot, ctx))
        markets_task = asyncio.create_task(refresh_markets_task(ctx, interval_seconds=3600))

        logging.info("Bot is up and running...")
        await dp.start_polling(bot)

    finally:
        for task in (alerts_task, markets_task):
            if task and not task.done():
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

        await http_session.close()
        await exchange.close()
        await bot.session.close()
        if hasattr(cache, "aclose"):
            await cache.aclose()
        else:
            await cache.close()


if __name__ == "__main__":
    try:
        asyncio.run(start_bot(), loop_factory=LOOP_FACTORY)
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    except Exception:
        logging.exception("Fatal error:")
        sys.exit(1)