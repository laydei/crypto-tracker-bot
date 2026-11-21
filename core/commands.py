from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
    BotCommandScopeChat,
)


LOCALIZED_COMMANDS = {
    "en": [
        BotCommand(command="start", description="Main menu and bot overview"),
        BotCommand(command="commands", description="Full list of bot commands"),
        BotCommand(command="price", description="Check cryptocurrency price"),
        BotCommand(command="chart", description="Generate candlestick chart"),
        BotCommand(command="top", description="View top gainers and losers"),
        BotCommand(command="funding", description="Check perpetual funding rates"),
        BotCommand(command="cal", description="Calculate a math expression"),
        BotCommand(command="alert", description="Set a price notification"),
        BotCommand(command="alerts", description="Manage active price alerts"),
        BotCommand(command="currency", description="Change display currencies"),
        BotCommand(command="pushover", description="Configure Pushover settings"),
        BotCommand(command="settings", description="Configure bot settings"),
        BotCommand(command="language", description="Select interface language"),
    ],
    "uk": [
        BotCommand(command="start", description="Головне меню та огляд можливостей"),
        BotCommand(command="commands", description="Повний список усіх команд"),
        BotCommand(command="price", description="Перевірити ціну криптовалюти"),
        BotCommand(command="chart", description="Побудувати свічковий графік"),
        BotCommand(command="top", description="Топ росту та падіння ринку"),
        BotCommand(command="funding", description="Перевірити ставку фандінгу"),
        BotCommand(command="cal", description="Порахувати математичний вираз"),
        BotCommand(command="alert", description="Створити сповіщення про ціну"),
        BotCommand(command="alerts", description="Керування активними сповіщеннями"),
        BotCommand(command="currency", description="Змінити валюти відображення"),
        BotCommand(command="pushover", description="Налаштування Pushover"),
        BotCommand(command="settings", description="Налаштування бота"),
        BotCommand(command="language", description="Обрати мову інтерфейсу"),
    ],
    "ru": [
        BotCommand(command="start", description="Главное меню и обзор возможностей"),
        BotCommand(command="commands", description="Полный список всех команд"),
        BotCommand(command="price", description="Проверить цену криптовалюты"),
        BotCommand(command="chart", description="Построить свечной график"),
        BotCommand(command="top", description="Топ роста и падения рынка"),
        BotCommand(command="funding", description="Проверить ставку фандинга"),
        BotCommand(command="cal", description="Посчитать математическое выражение"),
        BotCommand(command="alert", description="Создать уведомление о цене"),
        BotCommand(command="alerts", description="Управление активными уведомлениями"),
        BotCommand(command="currency", description="Изменить валюты отображения"),
        BotCommand(command="pushover", description="Настройки Pushover"),
        BotCommand(command="settings", description="Настройки бота"),
        BotCommand(command="language", description="Выбрать язык интерфейса"),
    ],
}


async def set_commands(bot: Bot):
    """Shows the slash command menu in private chats and keeps it hidden in groups."""
    await bot.set_my_commands(LOCALIZED_COMMANDS["en"], scope=BotCommandScopeAllPrivateChats())
    for lang_code, commands in LOCALIZED_COMMANDS.items():
        await bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats(), language_code=lang_code)

    # Disable pop-up slash command menu in group chats
    await bot.set_my_commands([], scope=BotCommandScopeAllGroupChats())


async def set_user_commands(bot: Bot, chat_id: int, lang_code: str):
    """Updates '/' command descriptions for a specific private chat immediately."""
    if chat_id < 0:
        return
    commands = LOCALIZED_COMMANDS.get(lang_code, LOCALIZED_COMMANDS["en"])
    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=chat_id))