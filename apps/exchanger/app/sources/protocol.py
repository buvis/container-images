from datetime import date
from typing import Protocol, Callable

from app.models import SymbolInfo, SymbolType


class RateSource(Protocol):
    @property
    def source_id(self) -> str:
        """Unique identifier for this source (e.g., 'fcs', 'cnb')."""
        ...

    def available_symbols(
        self, on_progress: Callable[[str], None] | None = None
    ) -> list[str]:
        """Return list of symbol names this source can provide."""
        ...

    def fetch_history(
        self,
        symbols: list[str],
        days: int,
        on_progress: Callable[[str], None] | None = None,
        symbol_types: dict[str, SymbolType] | None = None,
    ) -> dict[str, dict[str, float]]:
        """Fetch historical rates for symbols.

        Args:
            symbols: List of symbol names to fetch
            days: Number of days of history
            on_progress: Optional callback for progress updates
            symbol_types: Optional dict mapping symbol -> type. Allows caller
                         to pass types from DB (source of truth for metadata).

        Returns:
            Dict mapping symbol -> {date_str: rate}
        """
        ...

    def fetch_rate(self, symbol: str, dt: date) -> float | None:
        """Fetch single rate for a symbol on a specific date.

        Args:
            symbol: Symbol name
            dt: Date to fetch

        Returns:
            Rate value or None if not available
        """
        ...

    def list_symbols(
        self, on_progress: Callable[[str], None] | None = None
    ) -> list[SymbolInfo]:
        """List all symbols available from this source.

        Returns:
            List of SymbolInfo objects
        """
        ...

    def get_symbol_info(self, symbol: str) -> SymbolInfo | None:
        """Get info for a specific symbol.

        Args:
            symbol: Symbol name

        Returns:
            SymbolInfo or None if not found
        """
        ...
