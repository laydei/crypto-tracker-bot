import asyncio
import html
import logging
import math
import time
import uuid
from contextlib import suppress

import aiohttp
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.config import PUSHOVER_APP_TOKEN
from core.context import AppContext
import core.database as db
import core.language as lang
from core.permissions import is_group_chat

router = Router()

# Keep references to fire-and-forget background tasks to prevent garbage collection
_background_tasks: set[asyncio.Task] = set()


# External API

async def send_pushover_notification(
    user_key: str,
    message: str,
    title: str,
    http_session: aiohttp.ClientSession,
    sound: str = "siren",
) -> bool:
    """Dispatches a high-priority notification using the shared secure HTTP session."""
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": PUSHOVER_APP_TOKEN,
        "user": user_key,
        "message": message,
        "title": title,
        "html": "1",
        "sound": sound,
        "priority": "1",
    }

    try:
        async with http_session.post(url, data=data) as resp:
            res = await resp.json()
            return res.get("status") == 1
    except Exception as e:
        logging.error(f"Pushover notification failed: {e}")
        return False


async def _reply_private_only_notice(message: Message, bot: Bot):
    """Informs group users that alerts/Pushover work in private chat and provides a direct link button."""
    scope_id = message.chat.id
    bot_user = await bot.me()
    kb = InlineKeyboardBuilder()
    kb.button(
        text=lang.get_text(scope_id, "open_private_btn"),
        url=f"https://t.me/{bot_user.username}?start=alerts",
    )
    await message.reply(lang.get_text(scope_id, "group_alerts_disabled"), reply_markup=kb.as_markup())


# Data Processing

async def create_price_alert(message: Message, args: str, ctx: AppContext):
    """Parses user input, validates constraints, and persists a new price alert."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    thread_id = message.message_thread_id if message.is_topic_message else None

    if not args:
        return lang.get_text(user_id, "alert_usage"), False

    parts = args.strip().lower().split()
    if len(parts) < 2:
        return lang.get_text(user_id, "alert_invalid_fmt"), False

    ticker = parts[0]
    try:
        target_price = float(parts[1].replace(",", "."))
    except ValueError:
        return lang.get_text(user_id, "alert_nan"), False

    if math.isnan(target_price) or math.isinf(target_price) or target_price <= 0:
        return lang.get_text(user_id, "alert_nan"), False

    repeat = False
    interval = 5
    if len(parts) > 2 and parts[2] in ["r", "repeat"]:
        repeat = True
        if len(parts) > 3:
            try:
                interval = int(parts[3])
            except ValueError:
                return lang.get_text(user_id, "alert_invalid_fmt"), False
        if interval < 5:
            return lang.get_text(user_id, "alert_invalid_fmt"), False

    if db.count_user_alerts(user_id) >= 20:
        return lang.get_text(user_id, "alert_limit"), False

    symbol = None
    for sym, market in ctx.markets.items():
        if market.get("active") and market.get("spot") and market.get("quote") == "USDT":
            if market["base"].lower() == ticker:
                symbol = sym
                break

    if not symbol:
        return lang.get_text(user_id, "alert_not_found", ticker=html.escape(ticker.upper())), False

    try:
        ticker_data = await ctx.exchange.fetch_ticker(symbol)
        current_price = float(ticker_data["last"])
    except Exception as e:
        logging.error(f"Failed to fetch ticker {symbol} for alert creation: {e}")
        return lang.get_text(user_id, "alert_api_err"), False

    direction = "up" if target_price > current_price else "down"
    alert_id = str(uuid.uuid4())[:8]

    db.add_alert(
        alert_id=alert_id,
        user_id=user_id,
        chat_id=chat_id,
        thread_id=thread_id,
        symbol=ticker.upper(),
        symbol_binance=symbol,
        target=target_price,
        direction=direction,
        repeat=repeat,
        interval=interval,
    )

    r_text = lang.get_text(user_id, "alert_repeat_sfx", interval=interval) if repeat else ""
    return lang.get_text(
        user_id,
        "alert_created",
        ticker=html.escape(ticker.upper()),
        target=target_price,
        repeat=r_text,
    ), True


def clear_all_alerts(user_id: int):
    """Deletes all active alerts for the requested user from the database."""
    db.clear_user_alerts(user_id)
    return lang.get_text(user_id, "alert_all_deleted_popup"), lang.get_text(user_id, "alert_all_deleted_text")


# Keyboard Generation

def build_pushover_keyboard(user_id: int):
    """Generates the localized Pushover configuration menu."""
    user = db.get_user(user_id)
    method = user["pushover_method"]

    key_set = lang.get_text(user_id, "push_key_yes") if user["pushover_key"] else lang.get_text(user_id, "push_key_no")

    meth_tg = "🔵 " + lang.get_text(user_id, "push_only_tg") if method == "tg" else lang.get_text(user_id, "push_only_tg")
    meth_push = "🔵 " + lang.get_text(user_id, "push_only_push") if method == "pushover" else lang.get_text(user_id, "push_only_push")
    meth_both = "🔵 " + lang.get_text(user_id, "push_both") if method == "both" else lang.get_text(user_id, "push_both")

    b = InlineKeyboardBuilder()
    b.button(text=meth_tg, callback_data="pushmeth_tg")
    b.button(text=meth_push, callback_data="pushmeth_pushover")
    b.button(text=meth_both, callback_data="pushmeth_both")
    b.adjust(1)

    sound_text = lang.get_text(user_id, "push_sound_btn", sound=user["pushover_sound"])
    b.button(text=sound_text, callback_data="menu_push_sounds")

    back_btn = lang.get_text(user_id, "menu_back_btn")
    b.button(text=back_btn, callback_data="menu_settings")
    b.adjust(1, 1, 1)

    method_display = (
        meth_tg.replace("🔵 ", "")
        if method == "tg"
        else (meth_push.replace("🔵 ", "") if method == "pushover" else meth_both.replace("🔵 ", ""))
    )
    text = lang.get_text(user_id, "push_menu_title", key_set=key_set, method=method_display)

    return text, b.as_markup()


def build_pushover_sounds_keyboard(user_id: int):
    """Generates the localized sound selection keyboard for Pushover notifications."""
    user = db.get_user(user_id)
    current_sound = user["pushover_sound"]

    sounds = {
        "siren": "🚨 Siren",
        "pushover": "🔔 Pushover",
        "cashregister": "💸 Register",
        "alien": "👽 Alien",
        "gamelan": "🎵 Gamelan",
    }

    b = InlineKeyboardBuilder()
    for snd_code, snd_name in sounds.items():
        text = f"✅ {snd_name}" if snd_code == current_sound else snd_name
        b.button(text=text, callback_data=f"pushsnd_{snd_code}")

    b.adjust(2)
    b.row(InlineKeyboardButton(text=lang.get_text(user_id, "menu_back_btn"), callback_data="menu_pushover"))

    text = lang.get_text(user_id, "push_choose_sound")
    return text, b.as_markup()


def build_active_alerts_keyboard(user_id: int):
    """Generates a localized keyboard listing all active user alerts for deletion."""
    alerts = db.get_user_alerts(user_id)
    if not alerts:
        return None, lang.get_text(user_id, "alerts_no_active")

    builder = InlineKeyboardBuilder()
    for alert in alerts:
        sym = alert["symbol"]
        tgt = alert["target"]
        r = " r" if alert["repeat"] else ""

        btn_text = f"{sym} {tgt:g}{r}"
        if len(btn_text) > 13:
            btn_text = btn_text[:11] + ".."

        builder.button(text=btn_text, callback_data=f"askdel_{alert['id']}")

    builder.adjust(4)

    del_all_text = lang.get_text(user_id, "alert_del_all_btn")
    builder.row(InlineKeyboardButton(text=del_all_text, callback_data="delallalerts"))

    return builder.as_markup(), lang.get_text(user_id, "alerts_list_text")


def build_single_delete_keyboard(user_id: int, alert_id: str):
    """Generates the localized confirmation menu for deleting a specific alert."""
    alert = db.get_alert(user_id, alert_id)
    if not alert:
        return None, None

    r_text = lang.get_text(user_id, "alert_repeat_sfx", interval=alert["interval"]) if alert["repeat"] else ""
    text = lang.get_text(
        user_id,
        "alert_del_confirm_text",
        symbol=html.escape(alert["symbol"]),
        target=alert["target"],
        repeat=r_text,
    )

    builder = InlineKeyboardBuilder()
    builder.button(text=lang.get_text(user_id, "alert_del_yes_btn"), callback_data=f"confirmdel_{alert_id}_list")
    builder.button(text=lang.get_text(user_id, "alert_del_no_btn"), callback_data="canceldel")
    builder.adjust(2)

    return text, builder.as_markup()


def build_delete_all_keyboard(user_id: int):
    """Generates the localized confirmation menu for clearing all active alerts."""
    builder = InlineKeyboardBuilder()
    builder.button(text=lang.get_text(user_id, "alert_del_all_yes_btn"), callback_data="confirmdelall")
    builder.button(text=lang.get_text(user_id, "alert_del_no_btn"), callback_data="canceldel")
    builder.adjust(2)

    text = lang.get_text(user_id, "alert_del_all_confirm_text")
    return text, builder.as_markup()


# Command Handlers

@router.message(Command("pushover"))
async def handle_pushover_command(message: Message, command: CommandObject, bot: Bot):
    """Stores the user's Pushover API key in private chats; blocked in groups."""
    if is_group_chat(message):
        with suppress(TelegramBadRequest):
            await message.delete()
        await _reply_private_only_notice(message, bot)
        return

    user_id = message.from_user.id
    if not command.args:
        await message.reply(lang.get_text(user_id, "pushover_usage"))
        return

    user_key = command.args.strip()
    db.update_setting(user_id, "pushover_key", user_key)

    with suppress(TelegramBadRequest):
        await message.delete()

    text, kbd = build_pushover_keyboard(user_id)
    saved_msg = lang.get_text(user_id, "pushover_saved", text=text)
    await message.answer(saved_msg, reply_markup=kbd)


@router.message(Command("testpush"))
async def handle_testpush_command(message: Message, ctx: AppContext, bot: Bot):
    """Dispatches a localized test notification in private chats; blocked in groups."""
    if is_group_chat(message):
        await _reply_private_only_notice(message, bot)
        return

    user_id = message.from_user.id
    user = db.get_user(user_id)

    await message.reply(lang.get_text(user_id, "push_test_tg_sent"))

    if user["pushover_method"] in ["pushover", "both"] and user["pushover_key"]:
        push_msg = lang.get_text(user_id, "push_test_success_msg")
        push_title = lang.get_text(user_id, "push_test_title")

        success = await send_pushover_notification(
            user_key=user["pushover_key"],
            message=push_msg,
            title=push_title,
            http_session=ctx.http_session,
            sound=user["pushover_sound"],
        )
        if success:
            await message.answer(lang.get_text(user_id, "push_test_success_alert"))
        else:
            await message.answer(lang.get_text(user_id, "push_test_fail"))

    elif user["pushover_method"] == "tg":
        await message.answer(lang.get_text(user_id, "push_test_tg_only"))
    else:
        await message.answer(lang.get_text(user_id, "push_test_no_key"))


@router.message(Command("a", "alert"))
async def handle_alert_command(message: Message, command: CommandObject, ctx: AppContext, bot: Bot):
    """Processes user input to establish a new price alert in private chats."""
    if is_group_chat(message):
        await _reply_private_only_notice(message, bot)
        return

    msg_text, _ = await create_price_alert(message, command.args, ctx)
    await message.reply(msg_text)


@router.message(Command("alerts", "as"))
async def handle_check_alerts_command(message: Message, bot: Bot):
    """Retrieves and displays active alerts in private chats."""
    if is_group_chat(message):
        await _reply_private_only_notice(message, bot)
        return

    keyboard, text = build_active_alerts_keyboard(message.from_user.id)
    if keyboard:
        await message.reply(text, reply_markup=keyboard)
    else:
        await message.reply(text)


# Settings Callbacks

@router.callback_query(F.data == "menu_pushover")
async def handle_pushover_menu_callback(callback: CallbackQuery):
    """Displays the Pushover configuration menu."""
    if is_group_chat(callback):
        await callback.answer(lang.get_text(callback.message.chat.id, "group_alerts_disabled"), show_alert=True)
        return

    text, kbd = build_pushover_keyboard(callback.from_user.id)
    with suppress(TelegramBadRequest):
        await callback.message.edit_text(text, reply_markup=kbd)
    await callback.answer()


@router.callback_query(F.data.startswith("pushmeth_"))
async def handle_pushover_method_selection(callback: CallbackQuery):
    """Updates the preferred delivery method for notifications."""
    if is_group_chat(callback):
        await callback.answer(lang.get_text(callback.message.chat.id, "group_alerts_disabled"), show_alert=True)
        return

    method = callback.data.split("_")[1]
    db.update_setting(callback.from_user.id, "pushover_method", method)
    text, kbd = build_pushover_keyboard(callback.from_user.id)

    with suppress(TelegramBadRequest):
        await callback.message.edit_text(text, reply_markup=kbd)
    await callback.answer()


@router.callback_query(F.data == "menu_push_sounds")
async def handle_push_sounds_menu_callback(callback: CallbackQuery):
    """Displays the sound selection menu for Pushover."""
    if is_group_chat(callback):
        await callback.answer(lang.get_text(callback.message.chat.id, "group_alerts_disabled"), show_alert=True)
        return

    text, kbd = build_pushover_sounds_keyboard(callback.from_user.id)
    with suppress(TelegramBadRequest):
        await callback.message.edit_text(text, reply_markup=kbd)
    await callback.answer()


@router.callback_query(F.data.startswith("pushsnd_"))
async def handle_push_sound_selection(callback: CallbackQuery):
    """Saves the user's selected Pushover notification sound."""
    if is_group_chat(callback):
        await callback.answer(lang.get_text(callback.message.chat.id, "group_alerts_disabled"), show_alert=True)
        return

    snd = callback.data.split("_")[1]
    db.update_setting(callback.from_user.id, "pushover_sound", snd)
    text, kbd = build_pushover_sounds_keyboard(callback.from_user.id)

    with suppress(TelegramBadRequest):
        await callback.message.edit_text(text, reply_markup=kbd)
    await callback.answer()


# Alerts Deletion Callbacks

@router.callback_query(F.data.startswith("askdel_"))
async def handle_ask_delete_callback(callback: CallbackQuery):
    """Prompts the user to confirm the deletion of a specific alert."""
    if is_group_chat(callback):
        await callback.answer(lang.get_text(callback.message.chat.id, "group_alerts_disabled"), show_alert=True)
        return

    user_id = callback.from_user.id
    alert_id = callback.data.split("_")[1]
    text, keyboard = build_single_delete_keyboard(user_id, alert_id)

    if not text:
        await callback.answer(lang.get_text(user_id, "alert_not_exists"), show_alert=True)
        kbd, txt = build_active_alerts_keyboard(user_id)
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(txt, reply_markup=kbd)
        return

    with suppress(TelegramBadRequest):
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("confirmdel_"))
async def handle_confirm_delete_callback(callback: CallbackQuery):
    """Processes the confirmed deletion of a single price alert."""
    if is_group_chat(callback):
        await callback.answer(lang.get_text(callback.message.chat.id, "group_alerts_disabled"), show_alert=True)
        return

    user_id = callback.from_user.id
    parts = callback.data.split("_")
    alert_id = parts[1]
    source = parts[2] if len(parts) > 2 else "list"

    db.remove_alert(user_id, alert_id)
    await callback.answer(lang.get_text(user_id, "alert_deleted_alert"))

    if source == "notif":
        off_txt = lang.get_text(user_id, "alert_turned_off")
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(callback.message.html_text + off_txt, reply_markup=None)
    else:
        kbd, txt = build_active_alerts_keyboard(user_id)
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(txt, reply_markup=kbd)


@router.callback_query(F.data == "delallalerts")
async def handle_ask_delete_all_callback(callback: CallbackQuery):
    """Prompts the user to confirm the deletion of all active alerts."""
    if is_group_chat(callback):
        await callback.answer(lang.get_text(callback.message.chat.id, "group_alerts_disabled"), show_alert=True)
        return

    text, keyboard = build_delete_all_keyboard(callback.from_user.id)
    with suppress(TelegramBadRequest):
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "confirmdelall")
async def handle_confirm_delete_all_callback(callback: CallbackQuery):
    """Processes the confirmed deletion of all price alerts for the user."""
    if is_group_chat(callback):
        await callback.answer(lang.get_text(callback.message.chat.id, "group_alerts_disabled"), show_alert=True)
        return

    user_id = callback.from_user.id
    alert_msg, text = clear_all_alerts(user_id)
    await callback.answer(alert_msg, show_alert=True)
    with suppress(TelegramBadRequest):
        await callback.message.edit_text(text)


@router.callback_query(F.data == "canceldel")
async def handle_cancel_delete_callback(callback: CallbackQuery):
    """Cancels the deletion prompt and returns to the active alerts list."""
    if is_group_chat(callback):
        await callback.answer(lang.get_text(callback.message.chat.id, "group_alerts_disabled"), show_alert=True)
        return

    user_id = callback.from_user.id
    kbd, txt = build_active_alerts_keyboard(user_id)
    if kbd:
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(txt, reply_markup=kbd)
    else:
        with suppress(TelegramBadRequest):
            await callback.message.delete()
    await callback.answer()


# Background Tasks

async def _send_telegram_alert(bot: Bot, chat_id: int, thread_id: int | None, text: str, reply_markup) -> bool:
    """Sends a Telegram alert message, retrying once if Telegram returns RetryAfter."""
    for attempt in range(2):
        try:
            await bot.send_message(
                chat_id=chat_id,
                message_thread_id=thread_id,
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
            return True
        except TelegramRetryAfter as e:
            if attempt == 0:
                logging.warning(f"Telegram flood control for chat {chat_id}. Sleeping {e.retry_after}s.")
                await asyncio.sleep(e.retry_after)
            else:
                logging.error(f"Telegram alert dropped after RetryAfter for chat {chat_id}.")
                return False
        except TelegramForbiddenError:
            logging.warning(f"Bot blocked or kicked from chat {chat_id}. Removing its alerts.")
            db.remove_alerts_by_chat(chat_id)
            return False
        except Exception as e:
            logging.error(f"Failed to send Telegram alert to chat {chat_id}: {e}")
            return False
    return False


async def check_alerts_task(bot: Bot, ctx: AppContext):
    """Continuously monitors live market prices for active symbols and triggers alerts."""
    error_backoff = 5

    while True:
        try:
            all_alerts = db.get_all_alerts()
            if not all_alerts:
                error_backoff = 5
                await asyncio.sleep(5)
                continue

            symbols = list({alert["symbol_binance"] for alert in all_alerts})
            tickers = await ctx.exchange.fetch_tickers(symbols)
            current_time = time.time()
            error_backoff = 5

            for alert in all_alerts:
                symbol = alert["symbol_binance"]
                if symbol not in tickers:
                    continue

                last_price = tickers[symbol].get("last")
                if last_price is None:
                    continue

                current_price = float(last_price)
                target = alert["target"]
                direction = alert["direction"]
                interval = alert["interval"]
                last_triggered = alert["last_triggered"]

                if current_time - last_triggered < interval:
                    continue

                triggered = (direction == "up" and current_price >= target) or (
                    direction == "down" and current_price <= target
                )

                if not triggered:
                    continue

                user_id = alert["user_id"]
                chat_id = alert["chat_id"]
                thread_id = alert["thread_id"]
                alert_id = alert["id"]
                safe_symbol = html.escape(alert["symbol"])

                dir_up = lang.get_text(user_id, "alert_triggered_up")
                dir_down = lang.get_text(user_id, "alert_triggered_down")
                direction_text = dir_up if direction == "up" else dir_down

                user = db.get_user(user_id)
                method = user["pushover_method"]
                push_key = user["pushover_key"]
                user_sound = user["pushover_sound"]

                if method in ["tg", "both"]:
                    msg = lang.get_text(
                        user_id,
                        "alert_triggered_msg",
                        symbol=safe_symbol,
                        dir_text=direction_text,
                        target=target,
                        current=current_price,
                    )

                    reply_markup = None
                    if alert["repeat"]:
                        msg += lang.get_text(user_id, "alert_repeat_msg", interval=interval)
                        kb = InlineKeyboardBuilder()
                        btn_text = lang.get_text(user_id, "alert_turn_off_btn")
                        kb.button(text=btn_text, callback_data=f"confirmdel_{alert_id}_notif")
                        reply_markup = kb.as_markup()

                    await _send_telegram_alert(
                        bot=bot,
                        chat_id=chat_id,
                        thread_id=thread_id,
                        text=msg,
                        reply_markup=reply_markup,
                    )

                if method in ["pushover", "both"] and push_key:
                    push_msg = f"{safe_symbol} {direction_text} {target:g} USDT!\nPrice: {current_price:g} USDT"
                    push_title = f"🔔 {alert['symbol']} Alert!"

                    task = asyncio.create_task(
                        send_pushover_notification(
                            user_key=push_key,
                            message=push_msg,
                            title=push_title,
                            http_session=ctx.http_session,
                            sound=user_sound,
                        )
                    )
                    _background_tasks.add(task)
                    task.add_done_callback(_background_tasks.discard)

                if not alert["repeat"]:
                    db.remove_alert(user_id, alert_id)
                else:
                    db.update_alert_triggered(alert_id, current_time)

            await asyncio.sleep(5)

        except asyncio.CancelledError:
            raise
        except Exception:
            logging.exception(f"Unexpected error in check_alerts_task (retrying in {error_backoff}s):")
            await asyncio.sleep(error_backoff)
            error_backoff = min(error_backoff * 2, 60)