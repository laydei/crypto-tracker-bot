import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

import core.database as db


class UserAndThrottleMiddleware(BaseMiddleware):
    """Handles rate-limiting, anonymous admin support, and first-contact language detection."""

    def __init__(self, rate_limit: float = 0.6, group_rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self.group_rate_limit = group_rate_limit
        self._last_user_seen: Dict[int, float] = {}
        self._last_chat_seen: Dict[int, float] = {}
        self._op_counter = 0

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        chat = event.chat if isinstance(event, Message) else (event.message.chat if isinstance(event, CallbackQuery) and event.message else None)
        user = getattr(event, "from_user", None)

        if chat is None:
            return
        if user is None and not (isinstance(event, Message) and event.sender_chat):
            return

        now = time.monotonic()
        scope_id = chat.id
        user_id = user.id if user else scope_id

        # Periodic cleanup of stale entries to prevent unbounded memory growth
        self._op_counter += 1
        if self._op_counter >= 500:
            self._op_counter = 0
            cutoff = now - 60.0
            self._last_user_seen = {k: ts for k, ts in self._last_user_seen.items() if ts > cutoff}
            self._last_chat_seen = {k: ts for k, ts in self._last_chat_seen.items() if ts > cutoff}

        if isinstance(event, Message):
            # Per-user throttle
            if now - self._last_user_seen.get(user_id, 0.0) < self.rate_limit:
                return
            self._last_user_seen[user_id] = now

            # Additional chat-wide throttle for groups to prevent multi-user command spam
            if chat.type in ("group", "supergroup"):
                if now - self._last_chat_seen.get(scope_id, 0.0) < self.group_rate_limit:
                    return
                self._last_chat_seen[scope_id] = now

        lang_code = user.language_code if user else None
        db.init_user_if_missing(scope_id, lang_code)

        return await handler(event, data)