import logging
from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from core.redis_client import cache

GROUP_ANONYMOUS_BOT_ID = 1087968824


def is_group_chat(event: Message | CallbackQuery) -> bool:
    """Returns True if the event originated from a group or supergroup."""
    chat = event.chat if isinstance(event, Message) else event.message.chat
    return chat.type in ("group", "supergroup")


async def can_manage_chat_settings(bot: Bot, event: Message | CallbackQuery) -> bool:
    """Allows settings changes in private chats or by administrators/owners in groups."""
    chat = event.chat if isinstance(event, Message) else event.message.chat
    if chat.type == "private":
        return True

    # Support anonymous group admins posting on behalf of the group
    if isinstance(event, Message) and event.sender_chat and event.sender_chat.id == chat.id:
        return True

    user = event.from_user
    if not user:
        return False
    if user.id == GROUP_ANONYMOUS_BOT_ID:
        return True

    cache_key = f"admin:{chat.id}:{user.id}"
    try:
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached == "1"
    except Exception as e:
        logging.error(f"Redis get error in permissions: {e}")

    try:
        member = await bot.get_chat_member(chat.id, user.id)
        is_admin = member.status in ("creator", "administrator")
        try:
            await cache.setex(cache_key, 60, "1" if is_admin else "0")
        except Exception:
            pass
        return is_admin
    except Exception as e:
        logging.error(f"Failed to check admin status in chat {chat.id} for user {user.id}: {e}")
        return False