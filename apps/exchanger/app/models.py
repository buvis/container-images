from dataclasses import dataclass, field
from typing import Literal, Any

SymbolType = Literal["forex", "crypto"]
TaskStatus = Literal["running", "done", "error"]


@dataclass
class Symbol:
    provider: str
    symbol: str
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
    symbol: str
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


class ScheduledResponse(BaseModel):
    scheduled: bool
    message: str
    started: list[str] = Field(default_factory=list)
    already_running: list[str] = Field(default_factory=list)


class SymbolResponse(BaseModel):
    provider: str
    symbol: str
    name: str | None
    type: SymbolType


class ForexCryptoSymbolResponse(BaseModel):
    provider: str
    symbol: str
    name: str | None


class TaskStateResponse(BaseModel):
    status: TaskStatus
    message: str
    per_symbol: dict[str, int] | None = None
    rows_written: int | None = None
    symbols_added: int | None = None


class BackupResponse(BaseModel):
    filename: str
    timestamp: str
    rates_count: int
    symbols_count: int
    metadata_count: int


class BackupInfo(BaseModel):
    filename: str
    timestamp: str


class RestoreResponse(BaseModel):
    timestamp: str
    rates: int | None = None
    symbols: int | None = None
    metadata: int | None = None
