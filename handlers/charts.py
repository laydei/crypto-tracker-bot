import asyncio
import html
import io
import logging
import re
import threading
from contextlib import suppress

import matplotlib
matplotlib.use("Agg")  # Must be set before importing pyplot or mplfinance

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InputMediaPhoto, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from core.context import AppContext
import core.language as lang
from services.api_helpers import search_coingecko
import services.mplfinance_style as mplf_stl

router = Router()

# mplfinance relies on global pyplot state, so renders are serialized
_CHART_SEMAPHORE = asyncio.Semaphore(1)
_PLOT_LOCK = threading.Lock()


class ChartCallback(CallbackData, prefix="chart"):
    symbol: str
    timeframe: str
    limit: int
    volume: bool = False


CHART_TIMEFRAMES = {
    "15m": {"label": "1d", "limit": 96},
    "1h":  {"label": "5d", "limit": 120},
    "8h":  {"label": "1mo", "limit": 93},
    "1d":  {"label": "6mo", "limit": 186},
}


# Keyboard Generation

def get_chart_keyboard(symbol: str, active_tf: str, volume: bool) -> InlineKeyboardMarkup:
    """Builds the interactive keyboard for chart timeframe and volume toggles."""
    builder = InlineKeyboardBuilder()
    safe_symbol = symbol.replace("/", "_")
    for tf, data in CHART_TIMEFRAMES.items():
        btn_text = f"• {data['label']} •" if tf == active_tf else data['label']
        builder.button(
            text=btn_text,
            callback_data=ChartCallback(symbol=safe_symbol, timeframe=tf, limit=data['limit'], volume=volume).pack(),
        )
    builder.adjust(4)

    vol_text = "📊 Volumes: ON ✅" if volume else "📊 Volumes: OFF ❌"
    current_limit = CHART_TIMEFRAMES[active_tf]['limit']
    builder.row(
        InlineKeyboardButton(
            text=vol_text,
            callback_data=ChartCallback(symbol=safe_symbol, timeframe=active_tf, limit=current_limit, volume=not volume).pack(),
        )
    )

    spot_symbol = symbol.replace("/", "_")
    futures_symbol = symbol.replace("/", "")
    builder.row(
        InlineKeyboardButton(text="Spot (Binance)", url=f"https://www.binance.com/en/trade/{spot_symbol}?type=spot"),
        InlineKeyboardButton(text="Futures (Binance)", url=f"https://www.binance.com/en/futures/{futures_symbol}"),
    )
    return builder.as_markup()


# Data Processing

def _render_chart_sync(ohlcv_data: list, timeframe: str, volume: bool) -> io.BytesIO:
    """CPU-bound synchronous chart rendering executed in a worker thread."""
    with _PLOT_LOCK:
        df = pd.DataFrame(ohlcv_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        df.set_index('Timestamp', inplace=True)

        dt_format = '%H:%M' if timeframe == '15m' else '%d/%m'
        buf = io.BytesIO()

        fig, axlist = mpf.plot(
            df,
            type='candle',
            style=mplf_stl.custom_style,
            volume=volume,
            datetime_format=dt_format,
            xrotation=0,
            tight_layout=True,
            ylabel='pricer by ld',
            show_nontrading=True,
            returnfig=True,
        )
        try:
            if timeframe == '15m':
                axlist[0].xaxis.set_major_locator(mdates.HourLocator(interval=3))
                axlist[0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

            fig.savefig(buf, format='png', bbox_inches='tight')
        finally:
            plt.close(fig)

        buf.seek(0)
        return buf


async def create_chart(symbol: str, timeframe: str, limit: int, ctx: AppContext, volume: bool = False) -> io.BytesIO:
    """Fetches OHLCV data via the shared exchange client and renders the chart without blocking the event loop."""
    ohlcv_data = await ctx.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    async with _CHART_SEMAPHORE:
        return await asyncio.to_thread(_render_chart_sync, ohlcv_data, timeframe, volume)


# Command Handlers

@router.message(Command("chart", "c"))
async def chart(message: Message, command: CommandObject, ctx: AppContext):
    """Processes chart requests and generates the initial image response."""
    scope_id = message.chat.id

    if not command.args:
        await message.reply(lang.get_text(scope_id, "chart_usage"))
        return

    raw_query = command.args.strip()
    query_graph = raw_query.upper()
    if "/" not in query_graph:
        query_graph = f"{query_graph}/USDT"

    # Validate format and length before rendering so ChartCallback.pack() stays within Telegram's 64-byte limit
    if not re.fullmatch(r"[A-Z0-9]{1,15}/[A-Z0-9]{1,10}", query_graph):
        await message.reply(lang.get_text(scope_id, "chart_error"))
        return

    status_msg = await message.answer(lang.get_text(scope_id, "chart_generating"))

    coin_data = await search_coingecko(raw_query, ctx.http_session)
    token_name = coin_data["name"] if coin_data else raw_query.upper()

    safe_token_name = html.escape(token_name)
    safe_query_graph = html.escape(query_graph)

    try:
        buf = await create_chart(symbol=query_graph, timeframe="1h", limit=120, ctx=ctx, volume=False)
        photo = BufferedInputFile(buf.read(), filename="chart.png")
        media = InputMediaPhoto(
            media=photo,
            caption=f"<b><code>{safe_token_name}</code> — <code>{safe_query_graph}</code></b>",
        )
        keyboard = get_chart_keyboard(query_graph, "1h", volume=False)

        await status_msg.edit_media(media=media, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Chart generation failed for {query_graph}: {e}")
        await status_msg.edit_text(lang.get_text(scope_id, "chart_error"))


@router.callback_query(ChartCallback.filter())
async def process_chart(callback: CallbackQuery, callback_data: ChartCallback, ctx: AppContext):
    """Updates the existing chart message when timeframe or volume parameters change."""
    scope_id = callback.message.chat.id if callback.message else callback.from_user.id
    await callback.answer(lang.get_text(scope_id, "chart_updating"))

    symbol = callback_data.symbol.replace("_", "/")
    try:
        buf = await create_chart(
            symbol=symbol,
            timeframe=callback_data.timeframe,
            limit=callback_data.limit,
            ctx=ctx,
            volume=callback_data.volume,
        )
        photo = BufferedInputFile(buf.read(), filename="chart.png")
        media = InputMediaPhoto(media=photo, caption=callback.message.html_text)
        new_keyboard = get_chart_keyboard(symbol, callback_data.timeframe, callback_data.volume)

        with suppress(TelegramBadRequest):
            await callback.message.edit_media(media=media, reply_markup=new_keyboard)

    except Exception as e:
        logging.error(f"Error updating chart for {symbol}: {e}")