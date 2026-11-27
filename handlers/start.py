from contextlib import suppress
import html

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.commands import set_user_commands
import core.database as db
import core.language as lang
from core.permissions import can_manage_chat_settings, is_group_chat
from handlers.currencies import generate_currency_keyboard
from services import currency_service as cur_srv

router = Router()


# Keyboard Generation

def build_start_keyboard(scope_id: int) -> InlineKeyboardMarkup:
    """Generates the main start keyboard with 'Commands' and 'Settings' buttons."""
    builder = InlineKeyboardBuilder()
    builder.button(text=lang.get_text(scope_id, "menu_commands_btn"), callback_data="menu_commands")
    builder.button(text=lang.get_text(scope_id, "menu_settings_btn"), callback_data="menu_settings")
    builder.adjust(2)
    return builder.as_markup()


def build_settings_keyboard(scope_id: int, is_group: bool = False) -> InlineKeyboardMarkup:
    """Generates the settings menu, hiding personal Pushover options in group chats."""
    builder = InlineKeyboardBuilder()

    builder.button(text=lang.get_text(scope_id, "menu_language_btn"), callback_data="menu_language")
    builder.button(text=lang.get_text(scope_id, "menu_currencies_btn"), callback_data="menu_currencies")

    if not is_group:
        builder.button(text=lang.get_text(scope_id, "menu_pushover_btn"), callback_data="menu_pushover")
        builder.adjust(3)
    else:
        builder.adjust(2)

    return builder.as_markup()


def build_language_keyboard(scope_id: int) -> InlineKeyboardMarkup:
    """Generates the language selection keyboard with a checkmark on the active language."""
    current_lang = db.get_user(scope_id).get("language", "en")

    languages = {
        "en": "🇬🇧 English",
        "uk": "🇺🇦 Українська",
        "ru": "🇷🇺 Русский",
    }

    builder = InlineKeyboardBuilder()
    for code, name in languages.items():
        text = f"✅ {name}" if code == current_lang else name
        builder.button(text=text, callback_data=f"setlang_{code}")

    builder.button(text=lang.get_text(scope_id, "menu_back_btn"), callback_data="menu_settings")
    builder.adjust(1)

    return builder.as_markup()


# Command Handlers

@router.message(Command("start", "help", "menu"))
async def handle_start_command(message: Message, bot: Bot):
    """Displays the bot greeting localized for the private user or group."""
    scope_id = message.chat.id
    is_group = is_group_chat(message)

    if not is_group:
        user_lang = db.get_user(scope_id).get("language", "en")
        with suppress(TelegramBadRequest):
            await set_user_commands(bot, scope_id, user_lang)
        display_name = html.escape(message.from_user.first_name or "User")
    else:
        display_name = html.escape(message.chat.title or "Group")

    text = lang.get_text(scope_id, "start_greeting", name=display_name)
    keyboard = build_start_keyboard(scope_id)
    await message.reply(text, reply_markup=keyboard)


@router.message(Command("commands", "cmds"))
async def handle_commands_list(message: Message):
    """Displays the full command reference tailored to private or group chats."""
    scope_id = message.chat.id
    key = "commands_group" if is_group_chat(message) else "commands_private"
    await message.reply(lang.get_text(scope_id, key))


@router.message(Command("settings"))
async def handle_settings_command(message: Message, bot: Bot):
    """Opens settings for private users or group administrators."""
    scope_id = message.chat.id
    if not await can_manage_chat_settings(bot, message):
        await message.reply(lang.get_text(scope_id, "group_admin_only"))
        return

    text = lang.get_text(scope_id, "settings_greeting")
    keyboard = build_settings_keyboard(scope_id, is_group=is_group_chat(message))
    await message.reply(text, reply_markup=keyboard)


@router.message(Command("language", "l"))
async def handle_language_command(message: Message, bot: Bot):
    """Opens language selection for private users or group administrators."""
    scope_id = message.chat.id
    if not await can_manage_chat_settings(bot, message):
        await message.reply(lang.get_text(scope_id, "group_admin_only"))
        return

    await message.reply(lang.get_text(scope_id, "choose_language"), reply_markup=build_language_keyboard(scope_id))


@router.message(Command("shortcuts"))
async def handle_shortcuts_command(message: Message):
    """Displays command aliases."""
    await message.reply(lang.get_text(message.chat.id, "shortcuts_text"))


# Callback Handlers

@router.callback_query(F.data == "menu_commands")
async def handle_commands_callback(callback: CallbackQuery):
    """Displays the command list from the start inline button."""
    scope_id = callback.message.chat.id
    key = "commands_group" if is_group_chat(callback) else "commands_private"

    builder = InlineKeyboardBuilder()
    builder.button(text=lang.get_text(scope_id, "menu_settings_btn"), callback_data="menu_settings")

    with suppress(TelegramBadRequest):
        await callback.message.edit_text(lang.get_text(scope_id, key), reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "menu_settings")
async def handle_settings_callback(callback: CallbackQuery, bot: Bot):
    """Navigates to the settings menu if the user has permission."""
    scope_id = callback.message.chat.id
    if not await can_manage_chat_settings(bot, callback):
        await callback.answer(lang.get_text(scope_id, "group_admin_only"), show_alert=True)
        return

    text = lang.get_text(scope_id, "settings_greeting")
    keyboard = build_settings_keyboard(scope_id, is_group=is_group_chat(callback))

    with suppress(TelegramBadRequest):
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "menu_language")
async def handle_language_menu_callback(callback: CallbackQuery, bot: Bot):
    """Displays the language selection submenu."""
    scope_id = callback.message.chat.id
    if not await can_manage_chat_settings(bot, callback):
        await callback.answer(lang.get_text(scope_id, "group_admin_only"), show_alert=True)
        return

    with suppress(TelegramBadRequest):
        await callback.message.edit_text(
            lang.get_text(scope_id, "choose_language"),
            reply_markup=build_language_keyboard(scope_id),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("setlang_"))
async def handle_language_selection(callback: CallbackQuery, bot: Bot):
    """Updates the language preference for the private user or group."""
    scope_id = callback.message.chat.id
    if not await can_manage_chat_settings(bot, callback):
        await callback.answer(lang.get_text(scope_id, "group_admin_only"), show_alert=True)
        return

    new_lang = callback.data.split("_")[1]
    db.update_setting(scope_id, "language", new_lang)

    if not is_group_chat(callback):
        with suppress(TelegramBadRequest):
            await set_user_commands(bot, scope_id, new_lang)

    with suppress(TelegramBadRequest):
        await callback.message.edit_text(
            lang.get_text(scope_id, "choose_language"),
            reply_markup=build_language_keyboard(scope_id),
        )
    await callback.answer(lang.get_text(scope_id, "lang_changed"), show_alert=False)


@router.callback_query(F.data == "menu_currencies")
async def handle_currencies_menu_callback(callback: CallbackQuery, bot: Bot):
    """Opens the multi-currency selection menu for the user or group."""
    scope_id = callback.message.chat.id
    if not await can_manage_chat_settings(bot, callback):
        await callback.answer(lang.get_text(scope_id, "group_admin_only"), show_alert=True)
        return

    selected_curs = cur_srv.get_user_currencies(scope_id)

    with suppress(TelegramBadRequest):
        await callback.message.edit_text(
            lang.get_text(scope_id, "choose_currency"),
            reply_markup=generate_currency_keyboard(selected_curs, scope_id),
        )
    await callback.answer()