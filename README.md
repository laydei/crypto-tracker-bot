# Crypto Tracker Bot

[English](#features) | [Українська](#-українська-швидкий-старт) | [Русский](#-русский-быстрый-старт)

Telegram bot for real-time cryptocurrency price tracking, multi-currency conversion, interactive candlestick charts, market movers, perpetual funding rates, and price alerts (Telegram + Pushover). Works in both **private chats** and **group chats** (with admin-controlled group settings).

- **Python:** 3.12+ (tested on Python 3.14)
- **Stack:** `aiogram` 3.x · `ccxt` · `mplfinance` · `SQLAlchemy` · `Redis`

---

## Features

- **Live Prices & Multi-Currency Conversion:** Instant spot prices from Binance converted into up to 6 simultaneous fiat/crypto currencies (`USDT`, `USD`, `EUR`, `UAH`, `BTC`, `ETH`, etc.) via CoinGecko rates cached in Redis.
- **Interactive Candlestick Charts:** Timeframe switching (`1d`, `5d`, `1mo`, `6mo`) and volume overlay toggles rendered off the event loop in worker threads.
- **Market Analytics:** Top liquid gainers/losers (`/top`) and perpetual futures funding rates (`/funding`).
- **Price Alerts & Pushover:** One-time or repeating price alerts with mobile push notifications via Pushover (private chats only).
- **Built-in Safe Calculator:** AST-based math evaluator via `/cal` (and inline in private chats).
- **Group Chat Mode:** Per-group language and display currency settings restricted to group administrators; slash command pop-up menu stays hidden in groups to prevent chat clutter.
- **Multilingual UI:** English (`en`), Ukrainian (`uk`), and Russian (`ru`).

---

## Commands

| Command | Aliases | Scope | Description |
| :--- | :--- | :--- | :--- |
| `/start` | `/help`, `/menu` | Private & Group | Welcome message and main inline menu |
| `/commands` | `/cmds` | Private & Group | Full command reference tailored to the current chat |
| `/price <coin>` | `/p` | Private & Group | Current price (supports multipliers, e.g. `/p 2.5 eth`) |
| `/chart <coin>` | `/c` | Private & Group | Interactive candlestick chart |
| `/top <1-50> [h\|l]` | `/t` | Private & Group | Top 24h gainers (`h`) or losers (`l`) with >$1M volume |
| `/funding <coin>` | `/f` | Private & Group | USDT perpetual contract funding rate |
| `/cal <expr>` | `/calc` | Private & Group | Evaluate a math expression |
| `/currency` | — | Private & Group (Admins) | Select up to 6 active display currencies |
| `/language` | `/l` | Private & Group (Admins) | Switch interface language (`EN` / `UK` / `RU`) |
| `/settings` | — | Private & Group (Admins) | Open settings menu |
| `/alert <coin> <price> [r] [sec]` | `/a` | Private only | Create one-time or repeating (`r`) price alert |
| `/alerts` | `/as` | Private only | View and delete active alerts |
| `/pushover <user_key>` | — | Private only | Save personal Pushover User Key (auto-deletes message) |
| `/testpush` | — | Private only | Send a test Pushover notification |

---

## Architecture

```text
bot_tg/
├── main.py                  # Entry point, uvloop setup, shared AppContext lifecycle
├── requirements.in          # Direct project dependencies
├── requirements.txt         # Compiled lockfile with pinned transitive dependencies
├── requirements-dev.in      # Development & testing dependencies
├── pytest.ini               # Pytest configuration
├── core/
│   ├── config.py            # Environment variables, BASE_DIR, DB/Redis URLs
│   ├── context.py           # Shared ccxt exchange, markets dict, and aiohttp session
│   ├── database.py          # SQLAlchemy models (UserSettings, Alert) & schema checks
│   ├── redis_client.py      # Async Redis client for rate & ticker caching
│   ├── permissions.py       # Group admin verification (with Redis cache & anon admins)
│   ├── middlewares.py       # Per-user & per-group throttling + auto language detection
│   ├── commands.py          # Scoped slash commands (enabled in private, hidden in groups)
│   └── language.py          # EN / UK / RU localization dictionary
├── handlers/                # Aiogram routers (start, price, charts, top, funding, alerts, currencies)
├── services/
│   ├── api_helpers.py       # Binance market lookup, CoinGecko search, periodic market refresh
│   ├── currency_service.py  # Multi-currency conversion with positive/negative Redis caching
│   ├── calculator.py        # Safe AST arithmetic parser
│   └── mplfinance_style.py  # Custom dark theme for candlestick charts
└── tests/                   # Pytest unit tests (settings, database, calculator, alerts)
Architectural Notes & Limitations
Single-Instance Polling: Designed to run as a single process (dp.start_polling). Running multiple instances concurrently against the same SQLite database and Telegram token will cause Conflict: terminated by other getUpdates request and duplicate alert checks.

In-Memory State: Active Binance market metadata (ctx.markets), user settings cache, and throttling timestamps are stored in process memory and refreshed hourly or on restart.

SQLite Concurrency: Default storage uses local SQLite (bot_database.db), which is suitable for personal and small-to-medium group workloads. For heavy multi-group deployments, switch DATABASE_URL to PostgreSQL.

Redis Dependency: A running Redis server is required for exchange rate caching, /top ticker caching, and group admin permission caching.

API Keys Setup
1. Telegram Bot Token
Open Telegram and search for @BotFather.

Send /newbot, enter a display name, and choose a unique username ending in bot.

Copy the generated HTTP API Token.

2. Pushover App Token (optional, for mobile push alerts)
Register or log in at pushover.net.

Scroll down to Your Applications and click Create an Application/API Token.

Enter a name (e.g. Crypto Bot), accept the terms, and click Create Application.

Copy the generated API Token/Key.

Setup & Running
Clone the repository and create a virtual environment:

Bash
python3 -m venv .venv
source .venv/bin/activate
Install dependencies:

Bash
pip install -r requirements.txt
Create and configure the .env file:
Copy the template file in the project root (bot_tg/):

Bash
cp .env.example .env
Open the created .env file in any text editor and paste your keys:

Фрагмент коду
TELEGRAM_BOT_TOKEN="your_botfather_token"
PUSHOVER_APP_TOKEN="your_pushover_token"
REDIS_URL="redis://localhost:6379/0"
TELEGRAM_BOT_TOKEN — required, token from @BotFather.

PUSHOVER_APP_TOKEN — optional, application token from pushover.net (needed only if you use mobile push alerts).

REDIS_URL — optional, defaults to redis://localhost:6379/0.

Run the bot:

Bash
python3 main.py
Run unit tests:

Bash
pip install -r requirements-dev.in
pytest
🇺🇦 Українська (Швидкий старт)
Отримання токенів:

Telegram Bot Token: відкрий @BotFather у Telegram, надішли /newbot, вкажи ім'я та юзернейм (має закінчуватися на bot) і скопіюй отриманий токен.

Pushover App Token (за бажанням): зареєструйся на pushover.net, у розділі Your Applications натисни Create an Application/API Token і скопіюй ключ.

Створення віртуального середовища та встановлення залежностей:

Bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Налаштування файлу .env:
У кореневій папці проєкту (bot_tg/) скопіюй шаблон .env.example у файл .env:

Bash
cp .env.example .env
Відкрий файл .env у будь-якому текстовому редакторі та встав туди свої ключі:

Фрагмент коду
TELEGRAM_BOT_TOKEN="твій_токен_від_botfather"
PUSHOVER_APP_TOKEN="твій_токен_від_pushover"
REDIS_URL="redis://localhost:6379/0"
TELEGRAM_BOT_TOKEN — обов'язково, без нього бот не запуститься.

PUSHOVER_APP_TOKEN — за бажанням, потрібен лише для пуш-сповіщень на телефон через Pushover.

REDIS_URL — за бажанням, за замовчуванням використовується локальний redis://localhost:6379/0.

Запуск бота:

Bash
python3 main.py
🇷🇺 Русский (Быстрый старт)
Получение токенов:

Telegram Bot Token: открой @BotFather в Telegram, отправь /newbot, укажи имя и юзернейм (должен заканчиваться на bot) и скопируй полученный токен.

Pushover App Token (опционально): зарегистрируйся на pushover.net, в разделе Your Applications нажми Create an Application/API Token и скопируй ключ.

Создание виртуального окружения и установка зависимостей:

Bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Настройка файла .env:
В корневой папке проекта (bot_tg/) скопируй шаблон .env.example в файл .env:

Bash
cp .env.example .env
Открой файл .env в любом текстовом редакторе и вставь туда свои ключи:

Фрагмент коду
TELEGRAM_BOT_TOKEN="ваш_токен_от_botfather"
PUSHOVER_APP_TOKEN="ваш_токен_от_pushover"
REDIS_URL="redis://localhost:6379/0"
TELEGRAM_BOT_TOKEN — обязательно, без него бот не запустится.

PUSHOVER_APP_TOKEN — опционально, нужен только для пуш-уведомлений на телефон через Pushover.

REDIS_URL — опционально, по умолчанию используется локальный redis://localhost:6379/0.

Запуск бота:

Bash
python3 main.py