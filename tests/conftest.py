import os

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456:TEST_TOKEN")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import core.database as db


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    """Redirects all database operations to an isolated temporary SQLite DB per test."""
    test_db_path = tmp_path / "test_bot.db"
    test_engine = create_engine(f"sqlite:///{test_db_path}", echo=False)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    monkeypatch.setattr(db, "engine", test_engine)
    monkeypatch.setattr(db, "SessionLocal", TestSessionLocal)
    db._user_cache.clear()

    db.Base.metadata.create_all(bind=test_engine)
    yield
    db._user_cache.clear()
    test_engine.dispose()