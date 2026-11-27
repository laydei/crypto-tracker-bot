import html
import json
import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from core.context import AppContext
import core.language as lang
from core.redis_client import safe_get, safe_setex
from services import currency_service as cur_srv

router = Router()

TOP_CACHE_KEY = "top:usdt_spot_tickers"
TOP_CACHE_TTL = 20
MIN_QUOTE_VOLUME_USDT = 1_000_000.0  # Filter out illiquid micro-cap pairs (< $1M 24h volume)


# Data Processing

async def _get_cached_spot_tickers(ctx: AppContext) -> list[dict]:
    """Fetches liquid USDT spot tickers using a 20-second Redis cache."""
    cached = await safe_get(TOP_CACHE_KEY)
    if cached:
        return json.loads(cached)

    all_tickers = await ctx.exchange.fetch_tickers()
    valid_tickers = []

    for symbol, ticker in all_tickers.items():
        market = ctx.markets.get(symbol)
        if not (market and market.get("active") and market.get("spot") and market.get("quote") == "USDT"):
            continue

        pct = ticker.get("percentage")
        price = ticker.get("last")
        quote_vol = ticker.get("quoteVolume")

        if pct is None or price is None or quote_vol is None:
            continue
        if float(quote_vol) < MIN_QUOTE_VOLUME_USDT:
            continue

        valid_tickers.append({
            "symbol": symbol.replace("/USDT", ""),
            "price": float(price),
            "percentage": float(pct),
        })

    if valid_tickers:
        await safe_setex(TOP_CACHE_KEY, TOP_CACHE_TTL, json.dumps(valid_tickers))

    return valid_tickers


async def generate_top_message(args: str, user_id: int, ctx: AppContext) -> str:
    """Ranks and formats the top gaining or losing liquid cryptocurrencies."""
    parts = args.strip().lower().split() if args else []

    if not parts:
        return lang.get_text(user_id, "top_usage")

    try:
        limit = int(parts[0])
        direction = parts[1] if len(parts) > 1 else "h"

        if limit < 1 or limit > 50:
            return lang.get_text(user_id, "top_limit_err")
        if direction not in ["h", "l"]:
            return lang.get_text(user_id, "top_dir_err")
    except ValueError:
        return lang.get_text(user_id, "top_val_err")

    try:
        valid_tickers = await _get_cached_spot_tickers(ctx)
        if not valid_tickers:
            return lang.get_text(user_id, "top_fetch_err")

        if direction == "h":
            sorted_tickers = sorted(valid_tickers, key=lambda x: x["percentage"], reverse=True)
            title = f"📈 <b>{lang.get_text(user_id, 'top_gainers')} {limit}:</b>\n\n"
        else:
            sorted_tickers = sorted(valid_tickers, key=lambda x: x["percentage"], reverse=False)
            title = f"📉 <b>{lang.get_text(user_id, 'top_losers')} {limit}:</b>\n\n"

        primary_cur = cur_srv.get_user_currencies(user_id)[0]
        rate, sym = await cur_srv.get_single_rate_and_symbol(primary_cur, ctx.http_session)
        if rate is None:
            rate, sym = 1.0, "₮"

        top_tickers = sorted_tickers[:limit]
        msg_lines = [title]

        for i, t in enumerate(top_tickers, 1):
            pct_float = t["percentage"]
            current_raw_price = t["price"]

            # Guard against ZeroDivisionError if a coin drops -100%
            denom = 1 + (pct_float / 100)
            old_raw_price = current_raw_price / denom if denom > 0 else 0.0

            converted_current = current_raw_price * rate
            converted_old = old_raw_price * rate

            price_str = cur_srv.format_price(converted_current)
            old_price_str = cur_srv.format_price(converted_old)
            pct_str = f"+{pct_float:.2f}%" if pct_float > 0 else f"{pct_float:.2f}%"
            safe_symbol = html.escape(t["symbol"])

            msg_lines.append(
                f"<b>{i}. {safe_symbol}</b>: {price_str} (<s>{old_price_str}</s>) {sym} | {pct_str}"
            )

        return "\n".join(msg_lines)

    except Exception:
        logging.exception("Error generating /top message:")
        return lang.get_text(user_id, "top_global_err")


# Command Handlers

@router.message(Command("top", "t"))
async def cmd_top(message: Message, command: CommandObject, ctx: AppContext):
    """Handles requests to display top market movers."""
    scope_id = message.chat.id
    status_msg = await message.answer(lang.get_text(scope_id, "top_status_msg"))

    try:
        final_msg = await generate_top_message(command.args, scope_id, ctx)
        await status_msg.edit_text(final_msg)
    except Exception:
        logging.exception("Unhandled error in /top:")
        await status_msg.edit_text(lang.get_text(scope_id, "top_global_err"))