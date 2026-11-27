import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.exceptions import TelegramForbiddenError
import pytest

import core.database as db
from handlers import alerts as alerts_handler


@pytest.mark.asyncio
async def test_one_time_alert_preserved_when_telegram_delivery_fails(monkeypatch):
    user_id = 8001
    db.update_setting(user_id, "pushover_method", "tg")
    db.add_alert(
        alert_id="a_fail",
        user_id=user_id,
        chat_id=user_id,
        thread_id=None,
        symbol="BTC",
        symbol_binance="BTC/USDT",
        target=90000.0,
        direction="up",
        repeat=False,
        interval=5,
    )

    bot = SimpleNamespace(send_message=AsyncMock(side_effect=RuntimeError("Network timeout")))
    ctx = SimpleNamespace(
        exchange=SimpleNamespace(fetch_tickers=AsyncMock(return_value={"BTC/USDT": {"last": 91000.0}})),
        http_session=SimpleNamespace(),
    )

    # Stop background loop cleanly right after the first monitoring tick
    monkeypatch.setattr(alerts_handler.asyncio, "sleep", AsyncMock(side_effect=asyncio.CancelledError))

    with pytest.raises(asyncio.CancelledError):
        await alerts_handler.check_alerts_task(bot, ctx)

    # One-time alert must remain in DB to retry on the next tick
    remaining = db.get_user_alerts(user_id)
    assert len(remaining) == 1
    assert remaining[0]["id"] == "a_fail"


@pytest.mark.asyncio
async def test_one_time_alert_removed_after_successful_delivery(monkeypatch):
    user_id = 8002
    db.update_setting(user_id, "pushover_method", "tg")
    db.add_alert(
        alert_id="a_ok",
        user_id=user_id,
        chat_id=user_id,
        thread_id=None,
        symbol="ETH",
        symbol_binance="ETH/USDT",
        target=3000.0,
        direction="down",
        repeat=False,
        interval=5,
    )

    bot = SimpleNamespace(send_message=AsyncMock())
    ctx = SimpleNamespace(
        exchange=SimpleNamespace(fetch_tickers=AsyncMock(return_value={"ETH/USDT": {"last": 2950.0}})),
        http_session=SimpleNamespace(),
    )

    monkeypatch.setattr(alerts_handler.asyncio, "sleep", AsyncMock(side_effect=asyncio.CancelledError))

    with pytest.raises(asyncio.CancelledError):
        await alerts_handler.check_alerts_task(bot, ctx)

    bot.send_message.assert_awaited_once()
    assert db.get_user_alerts(user_id) == []


@pytest.mark.asyncio
async def test_repeating_alert_updates_last_triggered_instead_of_deleting(monkeypatch):
    user_id = 8003
    db.update_setting(user_id, "pushover_method", "tg")
    db.add_alert(
        alert_id="a_rep",
        user_id=user_id,
        chat_id=user_id,
        thread_id=None,
        symbol="SOL",
        symbol_binance="SOL/USDT",
        target=200.0,
        direction="up",
        repeat=True,
        interval=60,
    )

    bot = SimpleNamespace(send_message=AsyncMock())
    ctx = SimpleNamespace(
        exchange=SimpleNamespace(fetch_tickers=AsyncMock(return_value={"SOL/USDT": {"last": 205.0}})),
        http_session=SimpleNamespace(),
    )

    monkeypatch.setattr(alerts_handler.asyncio, "sleep", AsyncMock(side_effect=asyncio.CancelledError))

    with pytest.raises(asyncio.CancelledError):
        await alerts_handler.check_alerts_task(bot, ctx)

    alerts = db.get_user_alerts(user_id)
    assert len(alerts) == 1
    assert alerts[0]["last_triggered"] > 0


@pytest.mark.asyncio
async def test_forbidden_error_cleans_up_chat_alerts():
    user_id = 8004
    db.add_alert(
        alert_id="a_blk",
        user_id=user_id,
        chat_id=user_id,
        thread_id=None,
        symbol="BTC",
        symbol_binance="BTC/USDT",
        target=50000.0,
        direction="down",
        repeat=False,
        interval=5,
    )

    bot = SimpleNamespace(
        send_message=AsyncMock(side_effect=TelegramForbiddenError(method="sendMessage", message="Forbidden"))
    )

    sent = await alerts_handler._send_telegram_alert(bot, user_id, None, "test", None)
    assert sent is False
    assert db.get_user_alerts(user_id) == []