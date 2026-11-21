import asyncio
import json
import logging
import aiohttp

from core.context import AppContext
from core.redis_client import cache


def find_binance_symbol(ticker: str, markets: dict) -> str | None:
    """Locates the active USDT spot trading pair for a given ticker in local markets."""
    ticker_upper = ticker.strip().upper()
    direct_symbol = f"{ticker_upper}/USDT"

    market = markets.get(direct_symbol)
    if market and market.get("active") is not False and market.get("spot") is True:
        return direct_symbol

    for symbol, mkt in markets.items():
        if (
            mkt.get("base", "").upper() == ticker_upper
            and mkt.get("quote") == "USDT"
            and mkt.get("active") is not False
            and mkt.get("spot") is True
        ):
            return symbol
    return None


async def search_coingecko(query: str, http_session: aiohttp.ClientSession) -> dict | None:
    """Queries CoinGecko with Redis TTL caching and negative caching to prevent 429 rate limits."""
    query_lower = query.casefold().strip()
    if not query_lower or len(query_lower) > 40:
        return None

    cache_key = f"cg:search:{query_lower}"

    try:
        cached = await cache.get(cache_key)
        if cached == "NONE" or cached == "ERR":
            return None
        if cached is not None:
            return json.loads(cached)
    except Exception as e:
        logging.error(f"Redis get error in search_coingecko: {e}")

    url = "https://api.coingecko.com/api/v3/search"
    try:
        async with http_session.get(url, params={"query": query_lower}) as response:
            if response.status == 429:
                logging.warning("CoinGecko rate limit (429) hit. Applying 60s negative cache.")
                try:
                    await cache.setex(cache_key, 60, "ERR")
                except Exception:
                    pass
                return None

            response.raise_for_status()
            data = await response.json()

        coins = data.get("coins", [])
        matched_coin = None
        for coin in coins:
            if coin.get("name", "").casefold() == query_lower:
                matched_coin = coin
                break
        if not matched_coin:
            for coin in coins:
                if coin.get("symbol", "").casefold() == query_lower:
                    matched_coin = coin
                    break

        try:
            if matched_coin:
                # Cache valid metadata for 10 minutes
                await cache.setex(cache_key, 600, json.dumps(matched_coin))
            else:
                # Cache negative search result for 5 minutes
                await cache.setex(cache_key, 300, "NONE")
        except Exception as e:
            logging.error(f"Redis set error in search_coingecko: {e}")

        return matched_coin

    except Exception as e:
        logging.warning(f"CoinGecko search failed for '{query_lower}': {e}")
        try:
            await cache.setex(cache_key, 60, "ERR")
        except Exception:
            pass
        return None


async def refresh_markets_task(ctx: AppContext, interval_seconds: int = 3600):
    """Periodically reloads Binance markets in the background to pick up new listings."""
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await ctx.exchange.load_markets(reload=True)
            ctx.markets.clear()
            ctx.markets.update(ctx.exchange.markets)
            logging.info(f"Refreshed Binance markets ({len(ctx.markets)} symbols).")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logging.error(f"Failed to refresh Binance markets: {e}")