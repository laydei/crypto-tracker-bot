from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.types import CallbackQuery, Chat, Message, User
import pytest

import core.database as db
import core.language as lang
from handlers import alerts as alerts_handler
from services import currency_service as cur_srv


def _make_message(user_id: int, chat_id: int, chat_type: str = "private") -> Message:
    msg = Message(
        message_id=1,
        date=1700000000,
        chat=Chat(id=chat_id, type=chat_type),
        from_user=User(id=user_id, is_bot=False, first_name="Test"),
        text="/pushover",
    )
    object.__setattr__(msg, "reply", AsyncMock())
    object.__setattr__(msg, "answer", AsyncMock())
    object.__setattr__(msg, "delete", AsyncMock())
    return msg


def _make_callback(user_id: int, data: str, chat_type: str = "private") -> CallbackQuery:
    msg = _make_message(user_id=user_id, chat_id=user_id, chat_type=chat_type)
    object.__setattr__(msg, "edit_text", AsyncMock())
    cb = CallbackQuery(
        id="cb_1",
        from_user=User(id=user_id, is_bot=False, first_name="Test"),
        chat_instance="inst_1",
        data=data,
        message=msg,
    )
    object.__setattr__(cb, "answer", AsyncMock())
    return cb


# Database & General Settings

def test_default_user_settings():
    user = db.get_user(1001)
    assert user == {
        "language": "en",
        "currency": "usdt",
        "pushover_key": None,
        "pushover_method": "tg",
        "pushover_sound": "siren",
    }


@pytest.mark.parametrize(
    ("tg_lang", "expected"),
    [
        ("uk", "uk"),
        ("uk-UA", "uk"),
        ("ru", "ru"),
        ("ru-RU", "ru"),
        ("en", "en"),
        ("en-US", "en"),
        ("de", "en"),
        (None, "en"),
    ],
)
def test_init_user_if_missing_language_detection(tg_lang, expected):
    user_id = 2001
    db.init_user_if_missing(user_id, telegram_lang=tg_lang)
    assert db.get_user(user_id)["language"] == expected


def test_init_user_does_not_overwrite_existing_settings():
    user_id = 2002
    db.update_setting(user_id, "language", "uk")
    db.init_user_if_missing(user_id, telegram_lang="ru")
    assert db.get_user(user_id)["language"] == "uk"


def test_update_setting_persists_and_invalidates_cache():
    user_id = 2003
    assert db.get_user(user_id)["language"] == "en"

    db.update_setting(user_id, "language", "uk")
    db.update_setting(user_id, "currency", "usdt,uah,eur")
    db.update_setting(user_id, "pushover_key", "uTestKey123")
    db.update_setting(user_id, "pushover_method", "both")
    db.update_setting(user_id, "pushover_sound", "cashregister")

    db._user_cache.clear()
    reloaded = db.get_user(user_id)

    assert reloaded == {
        "language": "uk",
        "currency": "usdt,uah,eur",
        "pushover_key": "uTestKey123",
        "pushover_method": "both",
        "pushover_sound": "cashregister",
    }


def test_update_setting_ignores_disallowed_fields():
    user_id = 2004
    before = db.get_user(user_id)
    db.update_setting(user_id, "is_admin", "1")
    db.update_setting(user_id, "user_id", "9999")
    assert db.get_user(user_id) == before


def test_group_and_private_settings_are_isolated():
    private_user_id = 3001
    group_chat_id = -1001987654321

    db.update_setting(private_user_id, "language", "uk")
    db.update_setting(private_user_id, "currency", "usdt,uah")

    db.update_setting(group_chat_id, "language", "en")
    db.update_setting(group_chat_id, "currency", "usdt,btc,eth")

    assert db.get_user(private_user_id)["language"] == "uk"
    assert db.get_user(private_user_id)["currency"] == "usdt,uah"
    assert db.get_user(group_chat_id)["language"] == "en"
    assert db.get_user(group_chat_id)["currency"] == "usdt,btc,eth"


# Language Settings & Translations

def test_get_text_respects_user_language_and_fallback():
    user_id = 4001
    assert "Settings Menu" in lang.get_text(user_id, "settings_greeting")

    db.update_setting(user_id, "language", "uk")
    assert "Меню налаштувань" in lang.get_text(user_id, "settings_greeting")

    db.update_setting(user_id, "language", "ru")
    assert "Меню настроек" in lang.get_text(user_id, "settings_greeting")

    db.update_setting(user_id, "language", "es")
    assert "Settings Menu" in lang.get_text(user_id, "settings_greeting")


def test_all_languages_have_identical_translation_keys():
    en_keys = set(lang.TRANSLATIONS["en"].keys())
    uk_keys = set(lang.TRANSLATIONS["uk"].keys())
    ru_keys = set(lang.TRANSLATIONS["ru"].keys())

    assert en_keys == uk_keys, f"Mismatch between EN and UK keys: {en_keys ^ uk_keys}"
    assert en_keys == ru_keys, f"Mismatch between EN and RU keys: {en_keys ^ ru_keys}"


# Currency Display Settings

def test_currency_toggle_limits_and_persistence():
    user_id = 5001
    assert cur_srv.get_user_currencies(user_id) == ["usdt"]

    curs, status = cur_srv.toggle_user_currency(user_id, "usdt")
    assert status == "min_one"
    assert curs == ["usdt"]

    for code in ["usd", "eur", "uah", "btc", "eth"]:
        curs, status = cur_srv.toggle_user_currency(user_id, code)
        assert status == "added"

    assert len(cur_srv.get_user_currencies(user_id)) == 6

    curs, status = cur_srv.toggle_user_currency(user_id, "sol")
    assert status == "max_limit"
    assert "sol" not in cur_srv.get_user_currencies(user_id)

    curs, status = cur_srv.toggle_user_currency(user_id, "eur")
    assert status == "removed"
    assert "eur" not in cur_srv.get_user_currencies(user_id)


# Pushover Settings & Keyboards

def test_pushover_keyboards_reflect_current_settings():
    user_id = 6001
    db.update_setting(user_id, "language", "en")

    text_initial, kbd_initial = alerts_handler.build_pushover_keyboard(user_id)
    assert "Not set" in text_initial
    buttons_initial = [btn.text for row in kbd_initial.inline_keyboard for btn in row]
    assert "🔵 TG Only" in buttons_initial

    db.update_setting(user_id, "pushover_key", "uSecretKey123")
    db.update_setting(user_id, "pushover_method", "both")
    db.update_setting(user_id, "pushover_sound", "alien")

    text_updated, kbd_updated = alerts_handler.build_pushover_keyboard(user_id)
    assert "Set" in text_updated
    buttons_updated = [btn.text for row in kbd_updated.inline_keyboard for btn in row]
    assert "🔵 TG + Pushover" in buttons_updated
    assert any("alien" in b for b in buttons_updated)

    _, sound_kbd = alerts_handler.build_pushover_sounds_keyboard(user_id)
    sound_buttons = [btn.text for row in sound_kbd.inline_keyboard for btn in row]
    assert "✅ 👽 Alien" in sound_buttons


@pytest.mark.asyncio
async def test_pushover_command_and_callbacks_update_settings():
    user_id = 6002
    db.update_setting(user_id, "language", "en")

    # 1. /pushover <key> saves key and deletes sensitive message
    message = _make_message(user_id=user_id, chat_id=user_id, chat_type="private")
    command = SimpleNamespace(args="  uMyPushoverKey99  ")
    bot = SimpleNamespace(me=AsyncMock())

    await alerts_handler.handle_pushover_command(message, command, bot)

    assert db.get_user(user_id)["pushover_key"] == "uMyPushoverKey99"
    message.delete.assert_awaited_once()
    message.answer.assert_awaited_once()

    # 2. Method selection callback updates pushover_method
    callback_meth = _make_callback(user_id=user_id, data="pushmeth_pushover", chat_type="private")
    await alerts_handler.handle_pushover_method_selection(callback_meth)
    assert db.get_user(user_id)["pushover_method"] == "pushover"
    callback_meth.answer.assert_awaited_once()

    # 3. Sound selection callback updates pushover_sound
    callback_snd = _make_callback(user_id=user_id, data="pushsnd_gamelan", chat_type="private")
    await alerts_handler.handle_push_sound_selection(callback_snd)
    assert db.get_user(user_id)["pushover_sound"] == "gamelan"
    callback_snd.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_pushover_command_blocked_in_group_chat():
    user_id = 6003
    group_id = -100555666777

    message = _make_message(user_id=user_id, chat_id=group_id, chat_type="supergroup")
    command = SimpleNamespace(args="uShouldNotBeSaved")
    bot = SimpleNamespace(me=AsyncMock(return_value=SimpleNamespace(username="test_crypto_bot")))

    await alerts_handler.handle_pushover_command(message, command, bot)

    assert db.get_user(user_id)["pushover_key"] is None
    message.delete.assert_awaited_once()
    message.reply.assert_awaited_once()