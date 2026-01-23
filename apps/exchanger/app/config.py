import logging
import os
from dataclasses import dataclass, field

DEFAULT_DB_PATH = "/data/exchanger.db"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_AUTO_BACKFILL_TIME = "16:30"
DEFAULT_AUTO_BACKFILL_DAYS = 31
DEFAULT_SCHEDULER_TICK_SECONDS = 5.0
DEFAULT_RATE_LIMIT_WAIT = 65


@dataclass(frozen=True)
class Settings:
    provider_api_keys: dict[str, str] = field(default_factory=dict)
    db_path: str = DEFAULT_DB_PATH
    backup_dir: str = ""  # defaults to 'backups' subdir next to db_path
    symbols: dict[str, list[str]] = field(default_factory=dict)  # provider → symbols
    global_symbols: list[str] = field(default_factory=list)  # symbols to backfill from all providers
    auto_backfill_time: str = DEFAULT_AUTO_BACKFILL_TIME
    auto_backfill_days: int = DEFAULT_AUTO_BACKFILL_DAYS
    scheduler_tick_seconds: float = DEFAULT_SCHEDULER_TICK_SECONDS
    rate_limit_wait: int = DEFAULT_RATE_LIMIT_WAIT
    log_level: str = DEFAULT_LOG_LEVEL


def load_settings() -> Settings:
    from pathlib import Path

    provider_api_keys = _load_provider_api_keys()
    symbols, global_symbols = _parse_symbols(os.getenv("SYMBOLS", ""))

    db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
    # Default backup_dir to 'backups' subdir next to DB file
    default_backup_dir = str(Path(db_path).parent / "backups")
    backup_dir = os.getenv("BACKUP_DIR", default_backup_dir)

    return Settings(
        provider_api_keys=provider_api_keys,
        db_path=db_path,
        backup_dir=backup_dir,
        symbols=symbols,
        global_symbols=global_symbols,
        auto_backfill_time=os.getenv("AUTO_BACKFILL_TIME", DEFAULT_AUTO_BACKFILL_TIME),
        auto_backfill_days=_parse_int("AUTO_BACKFILL_DAYS", DEFAULT_AUTO_BACKFILL_DAYS),
        scheduler_tick_seconds=_parse_float(
            "SCHEDULER_TICK_SECONDS", DEFAULT_SCHEDULER_TICK_SECONDS
        ),
        rate_limit_wait=_parse_int("RATE_LIMIT_WAIT", DEFAULT_RATE_LIMIT_WAIT),
        log_level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
    )


def _parse_int(env_var: str, default: int) -> int:
    val = os.getenv(env_var)

    if val is None:
        return default

    try:
        return int(val)
    except ValueError:
        logging.warning("invalid %s=%r, using default %d", env_var, val, default)

        return default


def _parse_float(env_var: str, default: float) -> float:
    val = os.getenv(env_var)

    if val is None:
        return default

    try:
        return float(val)
    except ValueError:
        logging.warning("invalid %s=%r, using default %f", env_var, val, default)

        return default


def _parse_symbols(raw: str) -> tuple[dict[str, list[str]], list[str]]:
    """Parse SYMBOLS env var.

    Format: 'fcs:EURCZK,USDCZK,cnb:EURCZK'
    - 'provider:symbol' → backfill from specific provider
    - 'symbol' (no colon) → backfill from all providers that support it

    Returns:
        Tuple of (provider_symbols, global_symbols)
    """
    provider_symbols: dict[str, list[str]] = {}
    global_symbols: list[str] = []

    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            provider, symbol = item.split(":", 1)
            provider = provider.strip().lower()
            symbol = symbol.strip()
            if provider and symbol:
                provider_symbols.setdefault(provider, []).append(symbol)
        else:
            global_symbols.append(item)

    return provider_symbols, global_symbols


class UvicornFormatter(logging.Formatter):
    """Uvicorn-style colored formatter: LEVEL:     message"""

    COLORS = {
        "DEBUG": "\033[36m",     # cyan
        "INFO": "\033[32m",      # green
        "WARNING": "\033[33m",   # yellow
        "ERROR": "\033[31m",     # red
        "CRITICAL": "\033[1;31m", # bold red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        color = self.COLORS.get(levelname, "")
        # Match uvicorn's padding (9 chars for level + colon)
        padded = f"{levelname}:".ljust(9)
        msg = record.getMessage()
        return f"{color}{padded}{self.RESET} {msg}"


def configure_logging(level: str) -> None:
    """Configure logging with uvicorn-style colored output."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(UvicornFormatter())

    logging.root.handlers.clear()
    logging.root.addHandler(handler)
    logging.root.setLevel(numeric_level)

    # Ensure uvicorn loggers propagate to root
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True


def _load_provider_api_keys() -> dict[str, str]:
    """Load API keys from PROVIDER_<NAME>_API_KEY env vars."""
    prefix = "PROVIDER_"
    suffix = "_API_KEY"
    keys: dict[str, str] = {}

    for name, value in os.environ.items():
        if name.startswith(prefix) and name.endswith(suffix):
            provider = name[len(prefix) : -len(suffix)].lower()

            if value:
                keys[provider] = value

    return keys
