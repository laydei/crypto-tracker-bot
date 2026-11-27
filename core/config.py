import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PUSHOVER_APP_TOKEN = os.getenv("PUSHOVER_APP_TOKEN")

DEFAULT_DB_PATH = BASE_DIR / "bot_database.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {"en", "uk", "ru"}

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is missing from the .env file")