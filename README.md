# Crypto Tracker Bot

[English](#features) | [Українська](#-українська-швидкий-старт) | [Русский](#-русский-быстрый-старт)

Telegram bot for real-time cryptocurrency price tracking, multi-currency conversion, interactive candlestick charts, market movers, perpetual funding rates, and price alerts (Telegram + Pushover). Works in both **private chats** and **group chats** (with admin-controlled group settings).

- **Python:** 3.12+ (tested on Python 3.14)
- **Stack:** `aiogram` 3.x · `ccxt` · `mplfinance` · `SQLAlchemy` · `Redis`

---

## Features

- **Live Prices & Multi-Currency Conversion:** Instant spot prices from Binance converted into up to 6 simultaneous fiat/crypto currencies (`USDT`, `USD`, `EUR`, `UAH`, `BTC`, `ETH`, etc.) fetched concurrently via CoinGecko with Redis caching.
- **Interactive Candlestick Charts:** Timeframe switching (`1d`, `5d`, `1mo`, `6mo`) and volume overlay toggles rendered off the event loop in worker threads.
- **Market Analytics:** Top liquid gainers/losers (`/top`) and perpetual futures funding rates (`/funding`).
- **Price Alerts & Pushover:** One-time or repeating price alerts with mobile push notifications via Pushover (private chats only) and delivery-failure retry safety.
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
├── Dockerfile               # Non-root production container image
├── docker-compose.yml       # Bot + Redis stack with persistent named volume
├── pytest.ini               # Pytest configuration
├── core/
│   ├── config.py            # Environment variables, BASE_DIR, DB/Redis URLs
│   ├── context.py           # Shared ccxt exchange, markets dict, and aiohttp session
│   ├── database.py          # SQLAlchemy models (UserSettings, Alert) & schema checks
│   ├── redis_client.py      # Async Redis client with 30s circuit breaker fallback
│   ├── permissions.py       # Group admin verification (with Redis cache & anon admins)
│   ├── middlewares.py       # Per-user & per-group throttling + auto language detection
│   ├── commands.py          # Scoped slash commands (enabled in private, hidden in groups)
│   └── language.py          # EN / UK / RU localization dictionary
├── handlers/                # Aiogram routers (start, price, charts, top, funding, alerts, currencies)
├── services/
│   ├── api_helpers.py       # Binance market lookup, CoinGecko search, periodic market refresh
│   ├── currency_service.py  # Concurrent multi-currency conversion with positive/negative Redis caching
│   ├── calculator.py        # Safe AST arithmetic parser
│   └── mplfinance_style.py  # Custom dark theme for candlestick charts
└── tests/                   # Pytest unit tests (settings, i18n, calculator, cache/Redis, alerts)
Architectural Notes & Limitations
Single-Instance Polling: Designed to run as a single process (dp.start_polling). Running multiple instances concurrently against the same SQLite database and Telegram token will cause Conflict: terminated by other getUpdates request and duplicate alert checks.

In-Memory State: Active Binance market metadata (ctx.markets), user settings cache, and throttling timestamps are stored in process memory and refreshed hourly or on restart.

Database Storage: Uses local SQLite (bot_database.db) via SQLAlchemy with BigInteger Telegram IDs so schema migration to PostgreSQL (with psycopg/asyncpg) is straightforward if multi-group scale requires it.

Graceful Redis Degradation: Redis is used to cache CoinGecko exchange rates, /top ticker snapshots, and group admin permissions. If Redis is unreachable, safe_get/safe_setex open a 30-second circuit breaker and bypass cache calls immediately without blocking bot responses.

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
Option A: Local Run
Create a virtual environment and install dependencies:

Bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
Configure .env:

Bash
cp .env.example .env
Edit .env and set your keys:

Фрагмент коду
TELEGRAM_BOT_TOKEN="your_botfather_token"
PUSHOVER_APP_TOKEN="your_pushover_token"
REDIS_URL="redis://localhost:6379/0"
Run the bot & tests:

Bash
python3 main.py

# Run test suite (works without .env)
pip install -r requirements-dev.in
pytest -v
Option B: Docker Compose (Bot + Redis)
Bash
cp .env.example .env
# Fill TELEGRAM_BOT_TOKEN in .env
docker compose up -d --build
🇺🇦 Українська (Швидкий старт)
Отримання токенів:

Telegram Bot Token: відкрий @BotFather у Telegram, надішли /newbot, вкажи ім'я та юзернейм (має закінчуватися на bot) і скопіюй токен.

Pushover App Token (за бажанням): зареєструйся на pushover.net, у розділі Your Applications натисни Create an Application/API Token і скопіюй ключ.

Локальний запуск:

Bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Встав свої токени у .env
python3 main.py
(Якщо Redis не запущений локально, бот продовжить працювати завдяки 30-секундному circuit breaker).

Запуск через Docker Compose (бот + Redis):

Bash
cp .env.example .env
docker compose up -d --build
  Русский (Быстрый старт)
Получение токенов:

Telegram Bot Token: открой @BotFather в Telegram, отправь /newbot, укажи имя и юзернейм (должен заканчиваться на bot) и скопируй токен.

Pushover App Token (опционально): зарегистрируйся на pushover.net, в разделе Your Applications нажми Create an Application/API Token и скопируй ключ.

Локальный запуск:

Bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Вставь свои токены в .env
python3 main.py
(Если Redis не запущен локально, бот продолжит работу благодаря 30-секундному circuit breaker).

Запуск через Docker Compose (бот + Redis):

Bash
cp .env.example .env
docker compose up -d --build