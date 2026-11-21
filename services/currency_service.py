import logging
import aiohttp

import core.database as db
from core.redis_client import cache

FIAT_CURRENCIES = [
    "USDT", "USD", "EUR", "UAH",
    "GBP", "PLN", "CZK", "TRY",
    "KZT", "CAD", "AUD", "JPY",
    "CNY", "INR", "BRL", "GEL",
    "AMD", "AZN", "MDL", "CHF",
    "AED", "SEK", "NOK", "DKK",
    "RSD",
]

CRYPTO_CURRENCIES = [
    "BTC", "ETH", "BNB", "SOL",
    "TON", "XRP", "LTC", "LINK",
    "EOS", "BCH", "XLM", "YFI",
]

CURRENCY_SYMBOLS = {
    "usdt": "USDT", "usd": "$", "eur": "€", "uah": "₴",
    "gbp": "£", "pln": "zł", "czk": "Kč", "try": "₺",
    "kzt": "₸", "cad": "C$", "aud": "A$", "jpy": "¥",
    "cny": "¥", "inr": "₹", "brl": "R$", "gel": "₾",
    "amd": "֏", "azn": "₼", "mdl": "L", "chf": "CHF",
    "aed": "د.إ", "sek": "kr", "nok": "kr", "dkk": "kr",
    "rsd": "дин.", "btc": "BTC", "eth": "ETH", "ltc": "LTC",
}

MAX_SELECTED_CURRENCIES = 6


def get_user_currencies(user_id: int) -> list[str]:
    """Fetches the list of selected currency codes for the user."""
    raw = db.get_user(user_id).get("currency") or "usdt"
    currencies = [c.strip().lower() for c in raw.split(",") if c.strip()]
    return currencies if currencies else ["usdt"]


def toggle_user_currency(user_id: int, code: str) -> tuple[list[str], str]:
    """Toggles a currency in the user's active list (min 1, max 6)."""
    code = code.lower()
    current = get_user_currencies(user_id)

    if code in current:
        if len(current) == 1:
            return current, "min_one"
        current.remove(code)
        status = "removed"
    else:
        if len(current) >= MAX_SELECTED_CURRENCIES:
            return current, "max_limit"
        current.append(code)
        status = "added"

    db.update_setting(user_id, "currency", ",".join(current))
    return current, status


async def get_single_rate_and_symbol(
    currency_code: str,
    http_session: aiohttp.ClientSession,
) -> tuple[float | None, str]:
    """Fetches conversion rate using Redis (with negative caching) and the shared HTTP session."""
    code = currency_code.lower()
    symbol = CURRENCY_SYMBOLS.get(code, f"{code.upper()} ")

    if code == "usdt":
        return 1.0, symbol

    cache_key = f"rate:{code}"

    try:
        cached_val = await cache.get(cache_key)
        if cached_val == "ERROR":
            return None, symbol
        if cached_val is not None:
            return float(cached_val), symbol
    except Exception as e:
        logging.error(f"Redis get error for rate {code}: {e}")

    url = f"https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies={code}"

    try:
        async with http_session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            rate = float(data["tether"][code])

        try:
            await cache.setex(cache_key, 300, str(rate))
        except Exception as e:
            logging.error(f"Redis set error for rate {code}: {e}")

        return rate, symbol

    except Exception as e:
        logging.warning(f"Failed to fetch rate for {code}, caching negative result: {e}")
        try:
            await cache.setex(cache_key, 60, "ERROR")
        except Exception as redis_err:
            logging.error(f"Redis negative cache error for {code}: {redis_err}")

        return None, symbol


def format_price(price: float) -> str:
    """Formats the price with appropriate decimal places and thousands separators."""
    if price >= 1000:
        return f"{price:,.2f}".replace(",", " ")
    elif price >= 1:
        return f"{price:,.4f}".replace(",", " ").rstrip("0").rstrip(".")
    else:
        return f"{price:.8f}".rstrip("0").rstrip(".")


async def calculate_user_prices(
    user_id: int,
    raw_usdt_price: float,
    multiplier: float,
    http_session: aiohttp.ClientSession,
) -> list[tuple[str, str]]:
    """Returns a list of (formatted_price, symbol) tuples for all user-selected currencies."""
    selected = get_user_currencies(user_id)
    results = []

    for code in selected:
        rate, sym = await get_single_rate_and_symbol(code, http_session=http_session)
        if rate is None:
            continue
        final_val = raw_usdt_price * multiplier * rate
        results.append((format_price(final_val), sym))

    if not results:
        results.append((format_price(raw_usdt_price * multiplier), "₮"))

    return results