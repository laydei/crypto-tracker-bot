from dataclasses import dataclass
import aiohttp
import ccxt.async_support as ccxt


@dataclass
class AppContext:
    """Shared application dependencies injected into handlers via Aiogram workflow_data."""
    exchange: ccxt.Exchange
    markets: dict
    http_session: aiohttp.ClientSession