import html
import logging
import math

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from core.context import AppContext
import core.language as lang
from services.api_helpers import find_binance_symbol, search_coingecko
from services.calculator import process_math_expression
from services import currency_service as cur_srv

router = Router()


async def process_price_request(
    query: str,
    scope_id: int,
    ctx: AppContext,
    allow_name_search: bool = True,
) -> tuple[str | None, InlineKeyboardMarkup | None, bool]:
    """Processes price queries using local Binance markets first and formatting in the chat's currencies."""
    parts = query.strip().split()
    multiplier = 1.0
    search_text = ""

    if len(parts) == 1:
        search_text = parts[0]
    elif len(parts) == 2:
        try:
            multiplier = float(parts[0].replace(",", "."))
            search_text = parts[1]
        except ValueError:
            return None, None, False
    else:
        return None, None, False

    if math.isnan(multiplier) or math.isinf(multiplier) or multiplier <= 0:
        return None, None, False

    try:
        symbol = find_binance_symbol(search_text, ctx.markets)
        ticker = search_text.lower()
        name = search_text.upper()
        cg_url = f"https://www.coingecko.com/en/search?query={ticker}"

        if symbol:
            coin = await search_coingecko(ticker, ctx.http_session)
            if coin:
                name = coin.get("name", name)
                if coin.get("id"):
                    cg_url = f"https://www.coingecko.com/en/coins/{coin['id']}"
        else:
            if not allow_name_search:
                return None, None, False

            coin = await search_coingecko(search_text, ctx.http_session)
            if not coin:
                return None, None, False

            name = coin.get("name", search_text.upper())
            ticker = coin.get("symbol", "").lower()
            if coin.get("id"):
                cg_url = f"https://www.coingecko.com/en/coins/{coin['id']}"

            symbol = find_binance_symbol(ticker, ctx.markets)
            if not symbol:
                return None, None, False

        ticker_data = await ctx.exchange.fetch_ticker(symbol)
        last_price = ticker_data.get("last")
        if last_price is None:
            return None, None, False

        raw_price = float(last_price)
        price_entries = await cur_srv.calculate_user_prices(
            user_id=scope_id,
            raw_usdt_price=raw_price,
            multiplier=multiplier,
            http_session=ctx.http_session,
        )

        multiplier_text = ""
        if multiplier != 1.0:
            formatted_multiplier = cur_srv.format_price(multiplier)
            pieces_txt = lang.get_text(scope_id, "price_pieces")
            multiplier_text = f" ({formatted_multiplier}{pieces_txt})"

        raw_pct = ticker_data.get("percentage")
        if raw_pct is not None:
            pct_val = round(float(raw_pct), 2)
            change_str = f"+{pct_val}" if pct_val > 0 else str(pct_val)
        else:
            change_str = "0.0"

        safe_name = html.escape(name)
        first_price_str, first_sym = price_entries[0]

        lines = [
            f"<b>{safe_name}</b> ({ticker.upper()}){multiplier_text}:",
            f"<b>{first_price_str}</b> {first_sym}           | {change_str}%",
        ]
        for extra_price_str, extra_sym in price_entries[1:]:
            lines.append(f"<b>{extra_price_str}</b> {extra_sym}")

        text_msg = "\n".join(lines)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="CoinGecko", url=cg_url)]]
        )

        return text_msg, keyboard, True

    except Exception as e:
        logging.error(f"Error processing price request for '{query}': {e}")
        return None, None, False


# Command Handlers

@router.message(Command("price", "p"))
async def cmd_price(message: Message, command: CommandObject, ctx: AppContext):
    """Handles explicit /price commands in both private and group chats."""
    scope_id = message.chat.id

    if not command.args:
        await message.reply(lang.get_text(scope_id, "price_usage"))
        return

    text_msg, keyboard, success = await process_price_request(
        query=command.args,
        scope_id=scope_id,
        ctx=ctx,
        allow_name_search=True,
    )

    if success:
        await message.reply(text_msg, reply_markup=keyboard)
    else:
        await message.reply(lang.get_text(scope_id, "price_invalid"))


@router.message(Command("cal", "calc"))
async def cmd_calculator(message: Message, command: CommandObject):
    """Evaluates a math expression via explicit /cal command (works in groups and private chats)."""
    scope_id = message.chat.id
    if not command.args:
        await message.reply(lang.get_text(scope_id, "cal_usage"))
        return

    result = process_math_expression(command.args)
    if result:
        await message.reply(result)
    else:
        await message.reply(lang.get_text(scope_id, "cal_invalid"))


@router.message(F.text & ~F.text.startswith("/") & (F.chat.type == "private"))
async def token_price_private(message: Message, ctx: AppContext):
    """Intercepts plain text messages in private chats only for inline math or coin lookups."""
    query = message.text.strip()
    if len(query) > 60:
        return

    math_result = process_math_expression(query)
    if math_result:
        await message.reply(math_result)
        return

    text_msg, keyboard, success = await process_price_request(
        query=query,
        scope_id=message.chat.id,
        ctx=ctx,
        allow_name_search=True,
    )

    if success:
        await message.reply(text_msg, reply_markup=keyboard)