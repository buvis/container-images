from dataclasses import dataclass, field
from typing import Literal, Any

SymbolType = Literal["forex", "crypto"]
TaskStatus = Literal["running", "done", "error"]


@dataclass
class Symbol:
    provider: str
    symbol: str  # normalized symbol (e.g., EURCZK)
    provider_symbol: str  # provider-specific (e.g., EURCZK.ONE)
    type: SymbolType
    name: str | None = None
    id: int | None = None


@dataclass
class Rate:
    date: str
    symbol_id: int
    rate: float


@dataclass
class SymbolInfo:
    """Symbol info returned by rate sources (without provider/id)."""
    symbol: str  # normalized symbol (e.g., EURCZK)
    provider_symbol: str  # provider-specific (e.g., EURCZK.ONE)
    type: SymbolType
    name: str | None = None


@dataclass
class TaskState:
    status: TaskStatus
    message: str
    per_symbol: dict[str, int] = field(default_factory=dict)
    rows_written: int = 0

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"status": self.status, "message": self.message}
        if self.per_symbol:
            d["per_symbol"] = self.per_symbol
        if self.rows_written:
            d["rows_written"] = self.rows_written
        return d


@dataclass
class SymbolTaskState:
    status: TaskStatus
    message: str
    forex: int = 0
    crypto: int = 0

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"status": self.status, "message": self.message}
        if self.forex:
            d["forex"] = self.forex
        if self.crypto:
            d["crypto"] = self.crypto
        return d


# --- Pydantic response models for OpenAPI ---
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class RateResponse(BaseModel):
    rate: float | None


class RatesResponse(BaseModel):
    rates: dict[str, float | None]


class RateListItem(BaseModel):
    symbol: str  # normalized symbol
    provider_symbol: str  # provider-specific
    rate: float
    provider: str
    type: SymbolType


class RateHistoryItem(BaseModel):
    date: str
    rate: float | None


class ScheduledResponse(BaseModel):
    scheduled: bool
    message: str
    started: list[str] = Field(default_factory=list)
    already_running: list[str] = Field(default_factory=list)


class SymbolResponse(BaseModel):
    provider: str
    symbol: str  # normalized symbol
    provider_symbol: str  # provider-specific
    name: str | None
    type: SymbolType


class ForexCryptoSymbolResponse(BaseModel):
    provider: str
    symbol: str
    name: str | None


class TaskStateResponse(BaseModel):
    status: TaskStatus
    message: str
    last_run: str | None = None
    error: str | None = None
    per_symbol: dict[str, int] | None = None
    rows_written: int | None = None
    symbols_added: int | None = None
    progress: int | None = None  # 0-100 percentage
    progress_detail: str | None = None  # e.g., "2/5 symbols, page 3/4"
    rate_limit_until: str | None = None  # ISO timestamp when rate limit ends


class ProviderStatusResponse(BaseModel):
    name: str
    healthy: bool
    symbol_count: int
    symbol_counts_by_type: dict[str, int] = {}


class BackupResponse(BaseModel):
    filename: str
    timestamp: str
    rates_count: int
    symbols_count: int
    metadata_count: int
    favorites_count: int


class BackupInfo(BaseModel):
    filename: str
    timestamp: str


class RestoreResponse(BaseModel):
    timestamp: str
    rates: int | None = None
    symbols: int | None = None
    metadata: int | None = None
    favorites: int | None = None


class FrontendConfigResponse(BaseModel):
    dashboard_history_days: int


class FavoriteResponse(BaseModel):
    provider: str
    provider_symbol: str


class ChainRateResponse(BaseModel):
    from_rate: float | None
    from_provider: str
    from_symbol: str  # actual symbol used (may be inverted)
    from_inverted: bool  # True if we used inverted symbol (e.g., used BTCEUR for EUR→BTC)
    to_rate: float | None
    to_provider: str
    to_symbol: str  # actual symbol used (may be inverted)
    to_inverted: bool
    combined_rate: float | None
    intermediate: str  # the currency in the middle (e.g., EUR)
