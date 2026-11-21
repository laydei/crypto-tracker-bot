import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from core.config import DATABASE_URL, DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# In-memory cache for chat/user settings to avoid repeated SQLite queries
_user_cache: dict[int, dict] = {}


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(Integer, primary_key=True, index=True)
    language = Column(String, default=DEFAULT_LANGUAGE, nullable=False)
    currency = Column(String, default="usdt", nullable=False)
    pushover_key = Column(String, nullable=True)
    pushover_method = Column(String, default="tg", nullable=False)
    pushover_sound = Column(String, default="siren", nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(8), primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    chat_id = Column(Integer, nullable=False)
    thread_id = Column(Integer, nullable=True)
    symbol = Column(String(20), nullable=False)
    symbol_binance = Column(String(30), nullable=False)
    target = Column(Float, nullable=False)
    direction = Column(String(10), nullable=False)
    repeat = Column(Boolean, default=False)
    interval = Column(Integer, default=5)
    last_triggered = Column(Float, default=0.0)


def _ensure_schema():
    """Applies non-destructive column additions if an older SQLite database is detected."""
    inspector = inspect(engine)
    expected_columns = {
        "user_settings": {
            "language": f"VARCHAR DEFAULT '{DEFAULT_LANGUAGE}'",
            "currency": "VARCHAR DEFAULT 'usdt'",
            "pushover_key": "VARCHAR",
            "pushover_method": "VARCHAR DEFAULT 'tg'",
            "pushover_sound": "VARCHAR DEFAULT 'siren'",
        },
        "alerts": {
            "thread_id": "INTEGER",
            "repeat": "BOOLEAN DEFAULT 0",
            "interval": "INTEGER DEFAULT 5",
            "last_triggered": "FLOAT DEFAULT 0.0",
        },
    }

    with engine.begin() as conn:
        for table_name, columns in expected_columns.items():
            if not inspector.has_table(table_name):
                continue
            existing = {col["name"] for col in inspector.get_columns(table_name)}
            for col_name, col_ddl in columns.items():
                if col_name not in existing:
                    logging.info(f"Migrating schema: adding column {table_name}.{col_name}")
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_ddl}"))


def init_db():
    """Creates all database tables and verifies schema compatibility."""
    Base.metadata.create_all(bind=engine)
    _ensure_schema()


# --- User & Chat Settings Operations ---

def get_user(user_id: int) -> dict:
    """Fetches settings from cache or database, creating a default record if missing."""
    if user_id in _user_cache:
        return _user_cache[user_id].copy()

    with SessionLocal() as db:
        user = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not user:
            user = UserSettings(user_id=user_id, language=DEFAULT_LANGUAGE)
            db.add(user)
            db.commit()
            db.refresh(user)

        user_data = {
            "language": user.language or DEFAULT_LANGUAGE,
            "currency": user.currency or "usdt",
            "pushover_key": user.pushover_key,
            "pushover_method": user.pushover_method or "tg",
            "pushover_sound": user.pushover_sound or "siren",
        }
        _user_cache[user_id] = user_data
        return user_data.copy()


def update_setting(user_id: int, field: str, value: str):
    """Updates a specific setting and invalidates the cache."""
    allowed_fields = {"language", "currency", "pushover_key", "pushover_method", "pushover_sound"}
    if field not in allowed_fields:
        return

    get_user(user_id)

    with SessionLocal() as db:
        db.query(UserSettings).filter(UserSettings.user_id == user_id).update({field: value})
        db.commit()

    _user_cache.pop(user_id, None)


def init_user_if_missing(user_id: int, telegram_lang: str | None = None):
    """Creates a settings record on first contact using Telegram's language_code if supported."""
    if user_id in _user_cache:
        return

    with SessionLocal() as db:
        user = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not user:
            detected_lang = DEFAULT_LANGUAGE
            if telegram_lang:
                short_code = telegram_lang.split("-")[0].lower()
                if short_code in SUPPORTED_LANGUAGES:
                    detected_lang = short_code

            user = UserSettings(user_id=user_id, language=detected_lang)
            db.add(user)
            db.commit()
            db.refresh(user)

        _user_cache[user_id] = {
            "language": user.language or DEFAULT_LANGUAGE,
            "currency": user.currency or "usdt",
            "pushover_key": user.pushover_key,
            "pushover_method": user.pushover_method or "tg",
            "pushover_sound": user.pushover_sound or "siren",
        }


# --- Alerts Persistence Operations ---

def _alert_to_dict(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "user_id": alert.user_id,
        "chat_id": alert.chat_id,
        "thread_id": alert.thread_id,
        "symbol": alert.symbol,
        "symbol_binance": alert.symbol_binance,
        "target": alert.target,
        "direction": alert.direction,
        "repeat": alert.repeat,
        "interval": alert.interval,
        "last_triggered": alert.last_triggered,
    }


def count_user_alerts(user_id: int) -> int:
    """Returns the total number of active alerts for a user."""
    with SessionLocal() as db:
        return db.query(Alert).filter(Alert.user_id == user_id).count()


def add_alert(
    alert_id: str,
    user_id: int,
    chat_id: int,
    thread_id: int | None,
    symbol: str,
    symbol_binance: str,
    target: float,
    direction: str,
    repeat: bool,
    interval: int,
):
    """Persists a new price alert in the database."""
    with SessionLocal() as db:
        new_alert = Alert(
            id=alert_id,
            user_id=user_id,
            chat_id=chat_id,
            thread_id=thread_id,
            symbol=symbol,
            symbol_binance=symbol_binance,
            target=target,
            direction=direction,
            repeat=repeat,
            interval=interval,
            last_triggered=0.0,
        )
        db.add(new_alert)
        db.commit()


def get_user_alerts(user_id: int) -> list[dict]:
    """Retrieves all active alerts belonging to a specific user."""
    with SessionLocal() as db:
        alerts = db.query(Alert).filter(Alert.user_id == user_id).all()
        return [_alert_to_dict(a) for a in alerts]


def get_alert(user_id: int, alert_id: str) -> dict | None:
    """Retrieves a single alert by ID and user ID."""
    with SessionLocal() as db:
        alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user_id).first()
        return _alert_to_dict(alert) if alert else None


def get_all_alerts() -> list[dict]:
    """Retrieves all active alerts across all users for background monitoring."""
    with SessionLocal() as db:
        alerts = db.query(Alert).all()
        return [_alert_to_dict(a) for a in alerts]


def remove_alert(user_id: int, alert_id: str) -> bool:
    """Deletes a specific alert for a user."""
    with SessionLocal() as db:
        deleted = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user_id).delete()
        db.commit()
        return deleted > 0


def clear_user_alerts(user_id: int):
    """Deletes all active alerts for a user."""
    with SessionLocal() as db:
        db.query(Alert).filter(Alert.user_id == user_id).delete()
        db.commit()


def remove_alerts_by_chat(chat_id: int):
    """Deletes all alerts associated with a blocked or inaccessible chat."""
    with SessionLocal() as db:
        db.query(Alert).filter(Alert.chat_id == chat_id).delete()
        db.commit()


def update_alert_triggered(alert_id: str, timestamp: float):
    """Updates the last triggered timestamp for a repeating alert."""
    with SessionLocal() as db:
        db.query(Alert).filter(Alert.id == alert_id).update({"last_triggered": timestamp})
        db.commit()