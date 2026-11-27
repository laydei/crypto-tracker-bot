import json
from unittest.mock import AsyncMock, MagicMock

import pytest

import core.database as db
import core.redis_client as redis_client
from services import api_helpers
from services import currency_service as cur_srv


class _FakeResponse:
    def __init__(self, status: int, payload: dict):
        self.status = status
        self._payload = payload

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")

    async def json(self):
        return self._payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.fixture(autouse=True)
def reset_redis_circuit():
    redis_client._down_until = 0.0
    yield
    redis_client._down_until = 0.0


@pytest.mark.asyncio
async def test_redis_circuit_breaker_opens_on_failure_and_bypasses(monkeypatch):
    failing_get = AsyncMock(side_effect=ConnectionError("Redis connection refused"))
    failing_setex = AsyncMock(side_effect=ConnectionError("Redis connection refused"))

    monkeypatch.setattr(redis_client.cache, "get", failing_get)
    monkeypatch.setattr(redis_client.cache, "setex", failing_setex)

    # First call fails and trips the 30s circuit breaker
    assert await redis_client.safe_get("key:1") is None
    assert failing_get.await_count == 1

    # Subsequent calls bypass Redis immediately without waiting for socket timeout
    assert await redis_client.safe_get("key:2") is None
    await redis_client.safe_setex("key:2", 60, "value")

    assert failing_get.await_count == 1
    assert failing_setex.await_count == 0


@pytest.mark.asyncio
async def test_coingecko_negative_caching_on_429_prevents_repeated_requests(monkeypatch):
    memory_store: dict[str, tuple[int, str]] = {}

    async def fake_get(key: str):
        item = memory_store.get(key)
        return item[1] if item else None

    async def fake_setex(key: str, ttl: int, value: str):
        memory_store[key] = (ttl, value)

    monkeypatch.setattr(api_helpers, "safe_get", fake_get)
    monkeypatch.setattr(api_helpers, "safe_setex", fake_setex)

    session = MagicMock()
    session.get = MagicMock(return_value=_FakeResponse(status=429, payload={}))

    # 1st call hits CoinGecko and gets 429 -> caches "ERR" for 60s
    res1 = await api_helpers.search_coingecko("pepe", session)
    assert res1 is None
    assert session.get.call_count == 1
    assert memory_store["cg:search:pepe"] == (60, "ERR")

    # 2nd call hits negative cache -> 0 external HTTP calls
    res2 = await api_helpers.search_coingecko("PEPE", session)
    assert res2 is None
    assert session.get.call_count == 1


@pytest.mark.asyncio
async def test_coingecko_caches_valid_coin_and_not_found(monkeypatch):
    memory_store: dict[str, tuple[int, str]] = {}

    async def fake_get(key: str):
        item = memory_store.get(key)
        return item[1] if item else None

    async def fake_setex(key: str, ttl: int, value: str):
        memory_store[key] = (ttl, value)

    monkeypatch.setattr(api_helpers, "safe_get", fake_get)
    monkeypatch.setattr(api_helpers, "safe_setex", fake_setex)

    session = MagicMock()
    session.get = MagicMock(
        side_effect=[
            _FakeResponse(status=200, payload={"coins": [{"id": "solana", "name": "Solana", "symbol": "SOL"}]}),
            _FakeResponse(status=200, payload={"coins": []}),
        ]
    )

    coin = await api_helpers.search_coingecko("solana", session)
    assert coin["id"] == "solana"
    assert memory_store["cg:search:solana"][0] == 600
    assert json.loads(memory_store["cg:search:solana"][1])["symbol"] == "SOL"

    missing = await api_helpers.search_coingecko("unknowncoinxyz", session)
    assert missing is None
    assert memory_store["cg:search:unknowncoinxyz"] == (300, "NONE")


@pytest.mark.asyncio
async def test_calculate_user_prices_concurrent_conversion(monkeypatch):
    user_id = 7001
    db.update_setting(user_id, "currency", "usdt,usd,eur,uah")

    rates = {
        "usdt": (1.0, "USDT"),
        "usd": (0.999, "$"),
        "eur": (0.92, "€"),
        "uah": (41.5, "₴"),
    }

    async def fake_rate(code: str, http_session):
        return rates[code]

    monkeypatch.setattr(cur_srv, "get_single_rate_and_symbol", fake_rate)

    results = await cur_srv.calculate_user_prices(
        user_id=user_id,
        raw_usdt_price=100.0,
        multiplier=2.0,
        http_session=MagicMock(),
    )

    assert results == [
        ("200", "USDT"),
        ("199.8", "$"),
        ("184", "€"),
        ("8 300.00", "₴"),
    ]