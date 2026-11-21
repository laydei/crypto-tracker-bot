from contextlib import suppress

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import core.language as lang
from core.permissions import can_manage_chat_settings
from services import currency_service as cur_srv

router = Router()


# Keyboard Generation

def generate_currency_keyboard(selected_curs: list[str], scope_id: int) -> InlineKeyboardMarkup:
    """Generates the multi-select currency keyboard with checkmarks on all active currencies."""
    builder = InlineKeyboardBuilder()
    selected_set = {c.lower() for c in selected_curs}

    for cur in cur_srv.FIAT_CURRENCIES:
        text = f"✅ {cur}" if cur.lower() in selected_set else cur
        builder.button(text=text, callback_data=f"togglecur_{cur.lower()}")
    builder.adjust(4)

    crypto_title = lang.get_text(scope_id, "cur_crypto_title")
    builder.row(InlineKeyboardButton(text=crypto_title, callback_data="ignore_action"))

    crypto_builder = InlineKeyboardBuilder()
    for cur in cur_srv.CRYPTO_CURRENCIES:
        text = f"✅ {cur}" if cur.lower() in selected_set else cur
        crypto_builder.button(text=text, callback_data=f"togglecur_{cur.lower()}")
    crypto_builder.adjust(4)

    builder.attach(crypto_builder)

    back_btn = lang.get_text(scope_id, "menu_back_btn")
    builder.row(InlineKeyboardButton(text=back_btn, callback_data="menu_settings"))

    return builder.as_markup()


# Command Handlers

@router.message(Command("currency"))
async def handle_currency_command(message: Message, bot: Bot):
    """Opens the multi-currency selection menu for private users or group admins."""
    scope_id = message.chat.id
    if not await can_manage_chat_settings(bot, message):
        await message.reply(lang.get_text(scope_id, "group_admin_only"))
        return

    selected = cur_srv.get_user_currencies(scope_id)
    text = lang.get_text(scope_id, "choose_currency")
    keyboard = generate_currency_keyboard(selected, scope_id)

    await message.reply(text, reply_markup=keyboard)


# Callback Handlers

@router.callback_query(F.data.startswith("togglecur_"))
async def handle_toggle_currency(callback: CallbackQuery, bot: Bot):
    """Toggles a currency in the user's or group's active list."""
    scope_id = callback.message.chat.id
    if not await can_manage_chat_settings(bot, callback):
        await callback.answer(lang.get_text(scope_id, "group_admin_only"), show_alert=True)
        return

    code = callback.data.split("_", 1)[1]
    updated_list, status = cur_srv.toggle_user_currency(scope_id, code)

    if status == "min_one":
        await callback.answer("⚠️ Minimum 1 currency must remain selected.", show_alert=False)
        return
    if status == "max_limit":
        await callback.answer(f"⚠️ Maximum {cur_srv.MAX_SELECTED_CURRENCIES} currencies allowed.", show_alert=False)
        return

    text = lang.get_text(scope_id, "choose_currency")
    keyboard = generate_currency_keyboard(updated_list, scope_id)

    with suppress(TelegramBadRequest):
        await callback.message.edit_text(text, reply_markup=keyboard)

    active_display = ", ".join(c.upper() for c in updated_list)
    await callback.answer(f"✅ Active: {active_display}", show_alert=False)


@router.callback_query(F.data == "ignore_action")
async def handle_ignore_action(callback: CallbackQuery):
    """Silently ignores clicks on purely visual header buttons."""
    await callback.answer()