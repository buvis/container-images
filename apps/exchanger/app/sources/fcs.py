import logging
from datetime import date, datetime, timezone
from typing import Callable

from src import FcsApi  # fcsapi-rest package installs as 'src'

from app.models import SymbolInfo, SymbolType
from app.utils.retry import fetch_with_retry, is_shutting_down

logger = logging.getLogger(__name__)


class FcsSource:
    def __init__(self, api_key: str, rate_limit_wait: int = 65):
        self._api = FcsApi(api_key)
        self._rate_limit_wait = rate_limit_wait
        # Cache: symbol -> SymbolInfo (type + name)
        self._symbol_cache: dict[str, SymbolInfo] = {}

    @property
    def source_id(self) -> str:
        return "fcs"

    def available_symbols(
        self, on_progress: Callable[[str], None] | None = None
    ) -> list[str]:
        self._ensure_symbols_loaded(on_progress)
        return list(self._symbol_cache.keys())

    def set_symbol_cache(self, symbols: list[SymbolInfo]) -> None:
        """Set symbol cache from external source (e.g., after DB populate)."""
        self._symbol_cache = {s.symbol: s for s in symbols}

    def _ensure_symbols_loaded(
        self, on_progress: Callable[[str], None] | None = None
    ) -> None:
        """Lazy-load symbols if cache is empty.

        Raises:
            RuntimeError: If symbol loading fails (e.g., rate limited)
        """
        if self._symbol_cache:
            return
        logger.debug("lazy-loading symbols from API")
        if on_progress:
            on_progress("Loading available symbols...")
        symbols = self.list_symbols(on_progress)
        if not symbols:
            raise RuntimeError("Failed to load FCS symbols (possibly rate-limited)")
        self._symbol_cache = {s.symbol: s for s in symbols}
        logger.debug("loaded %d symbols into cache", len(self._symbol_cache))

    def fetch_history(
        self,
        symbols: list[str],
        days: int,
        on_progress: Callable[[str], None] | None = None,
        symbol_types: dict[str, SymbolType] | None = None,
    ) -> dict[str, dict[str, float]]:
        """Fetch historical rates for symbols.

        Args:
            symbols: List of symbol names
            days: Number of days of history
            on_progress: Optional progress callback
            symbol_types: Optional dict mapping symbol -> type. If provided, uses these
                         types instead of internal cache. This allows caller (e.g., backfill)
                         to pass types from DB.
        """
        logger.debug("fetch_history: symbols=%s days=%d", symbols, days)
        results: dict[str, dict[str, float]] = {}

        for symbol in symbols:
            if is_shutting_down():
                break
            # Get type from: 1) explicit param, 2) internal cache, 3) skip with warning
            sym_type = None
            if symbol_types and symbol in symbol_types:
                sym_type = symbol_types[symbol]
            elif symbol in self._symbol_cache:
                sym_type = self._symbol_cache[symbol].type

            if not sym_type:
                logger.warning("unknown symbol type for %s, skipping (populate symbols first)", symbol)
                continue

            rates = self._fetch_symbol_history(symbol, sym_type, days, on_progress)
            if rates:
                results[symbol] = rates
                logger.debug("fetched %d rates for %s (type=%s)", len(rates), symbol, sym_type)
            else:
                logger.debug("no rates found for %s", symbol)

        return results

    def _fetch_symbol_history(
        self,
        symbol: str,
        sym_type: SymbolType,
        length: int,
        on_progress: Callable[[str], None] | None,
    ) -> dict[str, float]:
        endpoint = f"{sym_type}/history"
        page = 1
        rates: dict[str, float] = {}
        remaining = length
        logger.debug("_fetch_symbol_history: symbol=%s type=%s length=%d", symbol, sym_type, length)

        while remaining > 0:
            if is_shutting_down():
                break
            page_length = min(remaining, 300)
            params = {"symbol": symbol, "period": "1D", "length": page_length, "page": page}

            if on_progress:
                on_progress(f"Fetching {symbol} page {page}...")

            logger.debug("requesting %s page=%d length=%d", endpoint, page, page_length)
            response = fetch_with_retry(
                self._api, endpoint, params, self._rate_limit_wait, on_progress
            )

            if not response or response.get("code") != 200:
                logger.debug("bad response from API: %s", response.get("code") if response else "None")
                break

            candles_data = response.get("response") or {}
            if not candles_data:
                logger.debug("no candles data in response")
                break

            candles = list(candles_data.values())
            logger.debug("received %d candles", len(candles))
            for candle in candles:
                day = self._unix_to_ymd(candle["t"])
                rate = float(candle["c"])
                rates[day] = rate

            if len(candles) < page_length:
                break

            remaining -= len(candles)
            page += 1

        return rates

    def fetch_rate(self, symbol: str, dt: date, symbol_type: SymbolType | None = None) -> float | None:
        """Fetch a single rate for a symbol on a specific date.

        Args:
            symbol: Symbol name
            dt: Date to fetch
            symbol_type: Optional explicit type. If not provided, uses internal cache.
        """
        # Get type from: 1) explicit param, 2) internal cache
        sym_type = symbol_type
        if not sym_type and symbol in self._symbol_cache:
            sym_type = self._symbol_cache[symbol].type

        if not sym_type:
            logger.warning("unknown symbol type for %s, cannot fetch rate (populate symbols first)", symbol)
            return None

        days_back = (date.today() - dt).days + 1
        length = max(1, min(days_back, 300))  # Cap at 300 (API limit)
        target_date = dt.strftime("%Y-%m-%d")

        endpoint = f"{sym_type}/history"
        params = {"symbol": symbol, "period": "1D", "length": length}

        response = fetch_with_retry(self._api, endpoint, params, self._rate_limit_wait)
        if not response or response.get("code") != 200:
            return None

        candles_data = response.get("response") or {}
        if not candles_data:
            return None

        candles = list(candles_data.values())
        for candle in candles:
            day = self._unix_to_ymd(candle["t"])
            if day == target_date:
                return float(candle["c"])

        return None

    def list_symbols(
        self, on_progress: Callable[[str], None] | None = None
    ) -> list[SymbolInfo]:
        symbols: list[SymbolInfo] = []

        for sym_type in ("forex", "crypto"):
            if is_shutting_down():
                break
            symbols.extend(self._fetch_symbols_of_type(sym_type, on_progress))

        return symbols

    def get_symbol_info(self, symbol: str) -> SymbolInfo | None:
        """Get symbol info from internal cache.

        Returns full SymbolInfo with type and name if symbol was loaded via
        list_symbols() or set_symbol_cache().
        """
        return self._symbol_cache.get(symbol)

    def _fetch_symbols_of_type(
        self,
        sym_type: SymbolType,
        on_progress: Callable[[str], None] | None = None,
    ) -> list[SymbolInfo]:
        endpoint = f"{sym_type}/list"
        page = 1
        symbols: list[SymbolInfo] = []

        while True:
            if is_shutting_down():
                break
            if on_progress:
                on_progress(f"Fetching {sym_type} page {page}...")

            response = fetch_with_retry(
                self._api, endpoint, {"page": page, "per_page": 1500}, self._rate_limit_wait, on_progress
            )

            if not response or response.get("code") != 200:
                break

            for item in response.get("response") or []:
                profile = item.get("profile") or {}
                sym = profile.get("symbol")
                name = profile.get("name")

                if not sym:
                    continue

                symbols.append(SymbolInfo(symbol=sym, type=sym_type, name=name))

            pagination = response.get("info", {}).get("pagination", {})
            if not pagination.get("has_next"):
                break

            page += 1

        return symbols

    @staticmethod
    def _unix_to_ymd(ts) -> str:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
