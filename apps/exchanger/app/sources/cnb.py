import logging
import time
import urllib.request
from datetime import date, timedelta
from typing import Callable

from app.models import SymbolInfo, SymbolType
from app.utils.retry import is_shutting_down

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 2


CNB_URL = "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"

# CNB publishes rates for these currencies (codes)
CNB_CURRENCIES = [
    "AUD", "BGN", "BRL", "CAD", "CHF", "CNY", "DKK", "EUR", "GBP", "HKD",
    "HUF", "IDR", "ILS", "INR", "ISK", "JPY", "KRW", "MXN", "MYR", "NOK",
    "NZD", "PHP", "PLN", "RON", "SEK", "SGD", "THB", "TRY", "USD", "XDR", "ZAR",
]

# Fallback names for currencies not in CNB daily response
CNB_CURRENCY_NAMES: dict[str, str] = {
    "AUD": "Australian dollar",
    "BGN": "Bulgarian lev",
    "BRL": "Brazilian real",
    "CAD": "Canadian dollar",
    "CHF": "Swiss franc",
    "CNY": "Chinese yuan",
    "DKK": "Danish krone",
    "EUR": "Euro",
    "GBP": "British pound",
    "HKD": "Hong Kong dollar",
    "HUF": "Hungarian forint",
    "IDR": "Indonesian rupiah",
    "ILS": "Israeli shekel",
    "INR": "Indian rupee",
    "ISK": "Icelandic krona",
    "JPY": "Japanese yen",
    "KRW": "South Korean won",
    "MXN": "Mexican peso",
    "MYR": "Malaysian ringgit",
    "NOK": "Norwegian krone",
    "NZD": "New Zealand dollar",
    "PHP": "Philippine peso",
    "PLN": "Polish zloty",
    "RON": "Romanian leu",
    "SEK": "Swedish krona",
    "SGD": "Singapore dollar",
    "THB": "Thai baht",
    "TRY": "Turkish lira",
    "USD": "US dollar",
    "XDR": "IMF Special Drawing Rights",
    "ZAR": "South African rand",
}


class CnbSource:
    def __init__(self, http_get: Callable[[str], str] | None = None, fetch_delay: float = 2.0):
        self._http_get = http_get or _default_http_get
        self._fetch_delay = fetch_delay
        self._symbol_names: dict[str, str] | None = None

    @property
    def source_id(self) -> str:
        return "cnb"

    def estimate_work_units(self, symbol_count: int, days: int) -> int:
        # Backfill service calls fetch_history once per symbol, each doing `days` API calls
        return symbol_count * days

    def available_symbols(
        self, on_progress: Callable[[str], None] | None = None
    ) -> list[str]:
        return [f"{code}CZK" for code in CNB_CURRENCIES]

    def fetch_history(
        self,
        symbols: list[str],
        days: int,
        on_progress: Callable[[str], None] | None = None,
        symbol_types: dict[str, SymbolType] | None = None,  # unused, CNB is forex-only
    ) -> dict[str, dict[str, float]]:
        logger.debug("fetch_history: symbols=%s days=%d", symbols, days)
        results: dict[str, dict[str, float]] = {sym: {} for sym in symbols}
        today = date.today()

        for day_offset in range(days):
            if is_shutting_down():
                break

            dt = today - timedelta(days=day_offset)
            rates = self._fetch_rates_for_date(dt)
            date_str = dt.strftime("%Y-%m-%d")
            logger.debug("fetched %d rates for %s", len(rates), date_str)

            for symbol in symbols:
                if symbol in rates:
                    results[symbol][date_str] = rates[symbol]

            # Signal work unit complete
            if on_progress:
                on_progress({"work_unit_done": True, "message": f"Fetched CNB {date_str}"})

            # Polite delay (except after last)
            if day_offset < days - 1 and not is_shutting_down() and self._fetch_delay > 0:
                time.sleep(self._fetch_delay)

        return results

    def fetch_rate(self, symbol: str, dt: date) -> float | None:
        rates = self._fetch_rates_for_date(dt)
        return rates.get(symbol)

    def list_symbols(
        self, on_progress: Callable[[str], None] | None = None
    ) -> list[SymbolInfo]:
        names = self._get_symbol_names()
        return [
            SymbolInfo(
                symbol=f"{code}CZK",
                provider_symbol=f"{code}CZK",
                type="forex",
                name=names.get(code, f"{CNB_CURRENCY_NAMES.get(code, code)} / Česká koruna"),
            )
            for code in CNB_CURRENCIES
        ]

    def get_symbol_info(self, provider_symbol: str) -> SymbolInfo | None:
        # CNB symbols are all forex, format: {CODE}CZK
        if provider_symbol.endswith("CZK") and provider_symbol[:-3] in CNB_CURRENCIES:
            code = provider_symbol[:-3]
            names = self._get_symbol_names()
            return SymbolInfo(symbol=provider_symbol, provider_symbol=provider_symbol, type="forex", name=names.get(code, f"{code}/CZK"))
        return None

    def _get_symbol_names(self) -> dict[str, str]:
        """Fetch and cache symbol names from CNB."""
        if self._symbol_names is not None:
            return self._symbol_names

        try:
            text = self._http_get(CNB_URL)
            self._symbol_names = _parse_symbol_names(text)
        except Exception as e:
            logger.warning("Failed to fetch CNB symbol names: %s", e)
            self._symbol_names = {}

        return self._symbol_names

    def _fetch_rates_for_date(self, dt: date) -> dict[str, float]:
        url = f"{CNB_URL}?date={dt.strftime('%d.%m.%Y')}"
        logger.debug("fetching CNB rates from %s", url)

        for attempt in range(MAX_RETRIES):
            try:
                text = self._http_get(url)
                return _parse_response(text)
            except Exception as e:
                logger.debug("CNB fetch attempt %d failed: %s", attempt + 1, e)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))

        logger.warning("CNB fetch failed after %d attempts for %s", MAX_RETRIES, dt)
        return {}


def _default_http_get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")


def _parse_response(text: str) -> dict[str, float]:
    """Parse CNB response text into {symbol: rate} dict.

    CNB format:
    20 Jan 2026 #15
    Country|Currency|Amount|Code|Rate
    Australia|dollar|1|AUD|16.021
    ...

    Note: Amount field indicates quantity (e.g., JPY uses 100).
    Rate is per Amount units, so we divide: rate = Rate / Amount.
    """
    rates: dict[str, float] = {}
    lines = text.strip().split("\n")

    # Skip header lines (date line + column headers)
    for line in lines[2:]:
        parts = line.split("|")
        if len(parts) != 5:
            continue

        try:
            amount = int(parts[2])
            code = parts[3].strip()
            rate_str = parts[4].strip().replace(",", ".")
            rate = float(rate_str)

            # Divide by amount to get rate per 1 unit
            if amount > 0:
                rate = rate / amount

            symbol = f"{code}CZK"
            rates[symbol] = rate
        except (ValueError, IndexError):
            continue

    return rates


def _parse_symbol_names(text: str) -> dict[str, str]:
    """Parse CNB response to extract symbol names.

    Format: "Country Currency / Česká koruna" (e.g., "Australia dollar / Česká koruna")
    """
    names: dict[str, str] = {}
    lines = text.strip().split("\n")

    for line in lines[2:]:
        parts = line.split("|")
        if len(parts) != 5:
            continue

        try:
            country = parts[0].strip()
            currency = parts[1].strip()
            code = parts[3].strip()
            names[code] = f"{country} {currency} / Česká koruna"
        except IndexError:
            continue

    return names
