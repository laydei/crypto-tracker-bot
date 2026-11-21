import logging
import html

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from core.context import AppContext
import core.language as lang
from services.api_helpers import search_coingecko

router = Router()


# Data Retrieval

async def get_funding_rate_str(ticker: str, ctx: AppContext, user_id: int) -> str:
    """Retrieves perpetual contract funding rate, distinguishing spot-only coins from network errors."""
    futures_symbol = f"{ticker.upper()}/USDT:USDT"

    # Check locally if a USDT perpetual contract exists before hitting the API
    if futures_symbol not in ctx.markets:
        err_msg = lang.get_text(user_id, "funding_error")
        return f"Funding: {err_msg}"

    try:
        funding_data = await ctx.exchange.fetch_funding_rate(futures_symbol)
        funding_rate = float(funding_data.get("fundingRate", 0)) * 100

        if funding_rate > 0:
            payer = lang.get_text(user_id, "funding_longs")
            return f"Funding: 🔴 {funding_rate:.4f}% ({payer})"
        elif funding_rate < 0:
            payer = lang.get_text(user_id, "funding_shorts")
            return f"Funding: 🟢 {funding_rate:.4f}% ({payer})"
        else:
            return "Funding: ⚪️ 0.0000%"
    except Exception as e:
        logging.error(f"Network/API error fetching funding rate for {futures_symbol}: {e}")
        err_msg = lang.get_text(user_id, "funding_global_err")
        return f"Funding: {err_msg}"


async def generate_funding_message(args: str, ctx: AppContext, user_id: int):
    """Generates the response message and keyboard for funding rate inquiries."""
    if not args:
        return lang.get_text(user_id, "funding_usage"), None

    ticker = args.strip().lower()
    funding_str = await get_funding_rate_str(ticker, ctx, user_id)

    safe_ticker = html.escape(ticker.upper())
    text = f"{safe_ticker}\n<i>{funding_str}</i>"

    keyboard = None
    coin = await search_coingecko(ticker, ctx.http_session)
    if coin and coin.get("id"):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="CoinGecko", url=f"https://www.coingecko.com/en/coins/{coin['id']}")]]
        )

    return text, keyboard


# Command Handlers

@router.message(Command("funding", "f"))
async def cmd_funding(message: Message, command: CommandObject, ctx: AppContext):
    """Handles the funding rate command to query futures market data."""
    scope_id = message.chat.id

    try:
        final_msg, keyboard = await generate_funding_message(command.args, ctx, scope_id)
        if keyboard:
            await message.reply(final_msg, reply_markup=keyboard)
        else:
            await message.reply(final_msg)
    except Exception:
        logging.exception("Unhandled error in /funding:")
        await message.reply(lang.get_text(scope_id, "funding_global_err"))