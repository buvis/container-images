import logging
import sqlite3
import threading
from datetime import date, timedelta
from typing import Protocol

from app.models import Rate, Symbol, SymbolType

logger = logging.getLogger(__name__)


class RatesRepository(Protocol):
    def get_rate(self, date: str, provider_symbol: str, provider: str) -> float | None: ...
    def get_rates_for_date(self, date: str, provider: str | None = None) -> list[dict]: ...
    def upsert_rate(self, date: str, provider_symbol: str, provider: str, rate: float) -> None: ...
    def get_symbol(self, provider_symbol: str, provider: str) -> Symbol | None: ...
    def list_symbols(self, provider: str | None = None, sym_type: SymbolType | None = None, query: str | None = None) -> list[Symbol]: ...
    def get_providers_for_symbol(self, symbol: str) -> list[str]: ...
    def export_rates(self) -> list[dict]: ...
    def export_symbols(self) -> list[dict]: ...
    def import_rates(self, rows: list[dict]) -> int: ...
    def import_symbols(self, rows: list[dict]) -> int: ...
    def commit(self) -> None: ...
    def close(self) -> None: ...


class SymbolsRepository(Protocol):
    def populate_symbols(self, provider: str, symbols: list[Symbol]) -> None: ...
    def commit(self) -> None: ...


SCHEMA_VERSION = 7


class SQLiteDatabase:
    def __init__(self, db_path: str):
        logger.debug("opening database at %s", db_path)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.Lock()
        self._closed = False
        self._init_db()
        logger.debug("database initialized")

    def _init_db(self) -> None:
        # Enable WAL mode for better concurrency
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._migrate_schema()
        self._conn.commit()

    def _migrate_schema(self) -> None:
        """Stepwise schema migrations."""
        version = self._get_schema_version()
        logger.debug("current schema version: %d, target: %d", version, SCHEMA_VERSION)

        if version == 0:
            self._migrate_v0_to_v7()
            version = 7
        elif version == 2:
            self._migrate_v2_to_v3()
            version = 3

        if version == 3:
            self._migrate_v3_to_v4()
            version = 4

        if version == 4:
            self._migrate_v4_to_v5()
            version = 5

        if version == 5:
            self._migrate_v5_to_v6()
            version = 6

        if version == 6:
            self._migrate_v6_to_v7()
            version = 7

        self._set_schema_version(version)

    def _migrate_v0_to_v7(self) -> None:
        """Fresh install - create v7 schema."""
        logger.debug("creating v7 schema")
        self._create_v7_schema()
        self._create_metadata_table()

    def _migrate_v4_to_v5(self) -> None:
        """Add symbol column (was normalized_symbol) and rename symbol to provider_symbol."""
        logger.debug("migrating v4 to v5: adding symbol/provider_symbol columns")
        # This migration is now handled by direct database changes
        # See exchanger.db schema - symbol is normalized, provider_symbol is provider-specific
        pass

    def _migrate_v5_to_v6(self) -> None:
        """Recreate favorites table with (provider, provider_symbol) composite key."""
        logger.debug("migrating v5 to v6: updating favorites table schema")
        # Export existing favorites (they only have normalized symbol, can't preserve)
        self._conn.execute("DROP TABLE IF EXISTS favorites")
        # Create old v6 schema temporarily (will be migrated to v7)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                provider_symbol TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(provider, provider_symbol)
            )
        """)

    def _migrate_v6_to_v7(self) -> None:
        """Migrate favorites to use symbol_id FK instead of provider/provider_symbol."""
        logger.debug("migrating v6 to v7: favorites with symbol_id FK")
        # Export existing favorites
        cur = self._conn.execute("SELECT provider, provider_symbol, created_at FROM favorites")
        old_favorites = cur.fetchall()

        # Drop old table and create new one
        self._conn.execute("DROP TABLE IF EXISTS favorites")
        self._create_favorites_table()

        # Re-import favorites by looking up symbol_id
        for provider, provider_symbol, created_at in old_favorites:
            cur = self._conn.execute(
                "SELECT id FROM symbols WHERE provider = ? AND provider_symbol = ?",
                (provider, provider_symbol),
            )
            row = cur.fetchone()
            if row:
                self._conn.execute(
                    "INSERT OR IGNORE INTO favorites (symbol_id, created_at) VALUES (?, ?)",
                    (row[0], created_at),
                )

    def _migrate_v2_to_v3(self) -> None:
        """Add metadata table."""
        logger.debug("migrating v2 to v3: adding metadata table")
        self._create_metadata_table()

    def _migrate_v3_to_v4(self) -> None:
        """Add favorites table."""
        logger.debug("migrating v3 to v4: adding favorites table")
        self._create_favorites_table()

    def _create_metadata_table(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

    def _create_favorites_table(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                symbol_id INTEGER PRIMARY KEY REFERENCES symbols(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _get_schema_version(self) -> int:
        cur = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        if not cur.fetchone():
            return 0  # Fresh DB
        cur = self._conn.execute("SELECT version FROM schema_version")
        row = cur.fetchone()
        return row[0] if row else 0

    def _set_schema_version(self, version: int) -> None:
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)"
        )
        self._conn.execute("DELETE FROM schema_version")
        self._conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))

    def _create_v2_schema(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                symbol TEXT NOT NULL,
                type TEXT NOT NULL,
                name TEXT,
                UNIQUE(provider, symbol)
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS rates (
                date TEXT NOT NULL,
                symbol_id INTEGER NOT NULL REFERENCES symbols(id),
                rate REAL NOT NULL,
                PRIMARY KEY(date, symbol_id)
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_provider ON symbols(provider)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(type)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_rates_date ON rates(date)")
        self._create_favorites_table()

    def _create_v5_schema(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                symbol TEXT NOT NULL,
                provider_symbol TEXT NOT NULL,
                type TEXT NOT NULL,
                name TEXT,
                UNIQUE(provider, provider_symbol)
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS rates (
                date TEXT NOT NULL,
                symbol_id INTEGER NOT NULL REFERENCES symbols(id),
                rate REAL NOT NULL,
                PRIMARY KEY(date, symbol_id)
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_provider ON symbols(provider)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(type)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_symbol ON symbols(symbol)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_rates_date ON rates(date)")
        self._create_favorites_table()

    def _create_v7_schema(self) -> None:
        # v7: favorites uses symbol_id FK
        self._create_v5_schema()

    def get_rate(self, date: str, provider_symbol: str, provider: str) -> float | None:
        with self._lock:
            if self._closed:
                return None
            cur = self._conn.execute(
                """
                SELECT r.rate FROM rates r
                JOIN symbols s ON r.symbol_id = s.id
                WHERE r.date = ? AND s.provider_symbol = ? AND s.provider = ?
                """,
                (date, provider_symbol, provider),
            )
            row = cur.fetchone()
            rate = row[0] if row else None
            logger.debug("get_rate: date=%s provider_symbol=%s provider=%s -> %s", date, provider_symbol, provider, rate)
            return rate

    def get_rates_for_date(self, date: str, provider: str | None = None) -> list[dict]:
        query = """
            SELECT s.symbol, s.provider_symbol, r.rate, s.provider, s.type
            FROM rates r
            JOIN symbols s ON r.symbol_id = s.id
            WHERE r.date = ?
        """
        params: list[str] = [date]

        if provider:
            query += " AND s.provider = ?"
            params.append(provider)

        query += " ORDER BY s.symbol ASC, s.provider ASC"

        with self._lock:
            if self._closed:
                return []
            cur = self._conn.execute(query, params)
            rows = cur.fetchall()

        return [
            {
                "symbol": row[0],
                "provider_symbol": row[1],
                "rate": row[2],
                "provider": row[3],
                "type": row[4],
            }
            for row in rows
        ]

    def get_rates_range(
        self,
        symbol: str,
        from_date: date,
        to_date: date,
        provider: str | None = None,
        provider_symbol: str | None = None,
    ) -> list[dict]:
        """Return daily rates for a symbol between two dates (inclusive).

        Args:
            symbol: Normalized symbol (used if provider_symbol not given)
            from_date: Start date
            to_date: End date
            provider: Optional provider filter
            provider_symbol: If provided, query by this exact provider_symbol instead of normalized symbol
        """
        if from_date > to_date:
            return []

        start = from_date.isoformat()
        end = to_date.isoformat()

        # Use provider_symbol for exact match if provided, otherwise use normalized symbol
        if provider_symbol:
            query = """
                SELECT r.date, r.rate
                FROM rates r
                JOIN symbols s ON r.symbol_id = s.id
                WHERE s.provider_symbol = ?
                  AND r.date BETWEEN ? AND ?
            """
            params: list[str] = [provider_symbol, start, end]
        else:
            query = """
                SELECT r.date, r.rate
                FROM rates r
                JOIN symbols s ON r.symbol_id = s.id
                WHERE s.symbol = ?
                  AND r.date BETWEEN ? AND ?
            """
            params = [symbol, start, end]

        if provider:
            query += " AND s.provider = ?"
            params.append(provider)

        query += " ORDER BY r.date ASC"

        with self._lock:
            if self._closed:
                return []
            cur = self._conn.execute(query, params)
            rows = cur.fetchall()

        rates_by_date: dict[str, float] = {}
        for date_str, rate in rows:
            rates_by_date.setdefault(date_str, rate)

        days = (to_date - from_date).days
        result: list[dict[str, float | None]] = []
        for i in range(days + 1):
            day = from_date + timedelta(days=i)
            day_str = day.isoformat()
            result.append({"date": day_str, "rate": rates_by_date.get(day_str)})

        return result

    def get_coverage(
        self,
        year: int,
        provider: str | None = None,
        symbols: list[str] | None = None,
    ) -> dict[str, int]:
        """Return how many rates exist for each date in a year (used by the heatmap)."""
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        query = """
            SELECT r.date, COUNT(*) as cnt
            FROM rates r
            JOIN symbols s ON r.symbol_id = s.id
            WHERE r.date BETWEEN ? AND ?
        """
        params: list[str] = [start.isoformat(), end.isoformat()]

        if provider:
            query += " AND s.provider = ?"
            params.append(provider)

        if symbols:
            placeholders = ", ".join(["?"] * len(symbols))
            query += f" AND s.symbol IN ({placeholders})"
            params.extend(symbols)

        query += " GROUP BY r.date ORDER BY r.date"

        with self._lock:
            if self._closed:
                return {}
            cur = self._conn.execute(query, params)
            rows = cur.fetchall()

        return {row[0]: int(row[1]) for row in rows}

    def get_missing_symbols(
        self,
        year: int,
        symbols: list[str],
        provider: str | None = None,
    ) -> dict[str, list[str]]:
        """Return missing symbols for each date in a year."""
        start = date(year, 1, 1)
        end = date(year, 12, 31)

        placeholders = ", ".join(["?"] * len(symbols))
        query = f"""
            SELECT r.date, s.symbol
            FROM rates r
            JOIN symbols s ON r.symbol_id = s.id
            WHERE r.date BETWEEN ? AND ?
            AND s.symbol IN ({placeholders})
        """
        params: list[str] = [start.isoformat(), end.isoformat(), *symbols]

        if provider:
            query += " AND s.provider = ?"
            params.append(provider)

        with self._lock:
            if self._closed:
                return {}
            cur = self._conn.execute(query, params)
            rows = cur.fetchall()

        # Build set of (date, symbol) pairs that exist
        existing: dict[str, set[str]] = {}
        for row in rows:
            dt, sym = row[0], row[1]
            if dt not in existing:
                existing[dt] = set()
            existing[dt].add(sym)

        # For each date with any data, find missing symbols
        symbol_set = set(symbols)
        result: dict[str, list[str]] = {}
        for dt, present in existing.items():
            missing = symbol_set - present
            if missing:
                result[dt] = sorted(missing)

        return result

    def upsert_rate(self, date: str, provider_symbol: str, provider: str, rate: float) -> bool:
        """Upsert rate. Returns True if inserted, False if symbol not found."""
        with self._lock:
            if self._closed:
                return False
            # Atomic insert with subquery - no race between SELECT and INSERT
            cur = self._conn.execute(
                """
                INSERT OR REPLACE INTO rates(date, symbol_id, rate)
                SELECT ?, id, ? FROM symbols WHERE provider_symbol = ? AND provider = ?
                """,
                (date, rate, provider_symbol, provider),
            )
            if cur.rowcount == 0:
                logger.warning("upsert_rate: provider_symbol %s not found for provider %s", provider_symbol, provider)
                return False
            logger.debug("upsert_rate: date=%s provider_symbol=%s provider=%s rate=%s", date, provider_symbol, provider, rate)
            return True

    def get_symbol(self, provider_symbol: str, provider: str) -> Symbol | None:
        with self._lock:
            if self._closed:
                return None
            cur = self._conn.execute(
                "SELECT id, provider, symbol, provider_symbol, type, name FROM symbols WHERE provider_symbol = ? AND provider = ?",
                (provider_symbol, provider),
            )
            row = cur.fetchone()
            if not row:
                return None
            return Symbol(id=row[0], provider=row[1], symbol=row[2], provider_symbol=row[3], type=row[4], name=row[5])

    def get_symbol_type(self, provider_symbol: str, provider: str) -> SymbolType | None:
        sym = self.get_symbol(provider_symbol, provider)
        return sym.type if sym else None

    def list_symbols(
        self,
        provider: str | None = None,
        sym_type: SymbolType | None = None,
        query: str | None = None,
    ) -> list[Symbol]:
        with self._lock:
            if self._closed:
                return []

            conditions = []
            params: list = []

            if provider:
                conditions.append("provider = ?")
                params.append(provider)

            if sym_type:
                conditions.append("type = ?")
                params.append(sym_type)

            if query:
                conditions.append("(provider_symbol LIKE ? OR name LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            cur = self._conn.execute(
                f"SELECT id, provider, symbol, provider_symbol, type, name FROM symbols {where_clause} ORDER BY name",
                params,
            )
            return [
                Symbol(id=row[0], provider=row[1], symbol=row[2], provider_symbol=row[3], type=row[4], name=row[5])
                for row in cur.fetchall()
            ]

    def get_providers_for_symbol(self, symbol: str) -> list[str]:
        """Get all providers that have this symbol in DB."""
        with self._lock:
            if self._closed:
                return []
            cur = self._conn.execute(
                "SELECT DISTINCT provider FROM symbols WHERE symbol = ?",
                (symbol,),
            )
            return [row[0] for row in cur.fetchall()]

    def list_multi_provider_symbols(self) -> list[dict]:
        """Get symbols available from multiple providers.

        Returns list of dicts with symbol and list of providers.
        """
        with self._lock:
            if self._closed:
                return []
            cur = self._conn.execute("""
                SELECT symbol, GROUP_CONCAT(DISTINCT provider) as providers, COUNT(DISTINCT provider) as cnt
                FROM symbols
                WHERE symbol IS NOT NULL
                GROUP BY symbol
                HAVING cnt > 1
                ORDER BY symbol
            """)
            return [
                {"symbol": row[0], "providers": row[1].split(",")}
                for row in cur.fetchall()
            ]

    def get_symbol_variants(self, symbol: str) -> list[Symbol]:
        """Get all provider variants for a symbol."""
        with self._lock:
            if self._closed:
                return []
            cur = self._conn.execute(
                "SELECT id, provider, symbol, provider_symbol, type, name FROM symbols WHERE symbol = ?",
                (symbol,),
            )
            return [
                Symbol(id=row[0], provider=row[1], symbol=row[2], provider_symbol=row[3], type=row[4], name=row[5])
                for row in cur.fetchall()
            ]

    def populate_symbols(self, provider: str, symbols: list[Symbol]) -> None:
        """Sync symbols for a provider - adds new, updates changed, removes stale.

        Uses a temp table for atomic comparison and update.
        """
        with self._lock:
            if self._closed:
                return

            logger.debug("populate_symbols: provider=%s, incoming=%d symbols", provider, len(symbols))

            # Create temp table for staging incoming symbols
            self._conn.execute("""
                CREATE TEMP TABLE IF NOT EXISTS _incoming_symbols (
                    provider_symbol TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    type TEXT NOT NULL,
                    name TEXT
                )
            """)

            try:
                # Clear temp table and populate with incoming data
                self._conn.execute("DELETE FROM _incoming_symbols")
                for s in symbols:
                    self._conn.execute(
                        "INSERT OR REPLACE INTO _incoming_symbols (provider_symbol, symbol, type, name) VALUES (?, ?, ?, ?)",
                        (s.provider_symbol, s.symbol, s.type, s.name),
                    )

                # Use savepoint for atomic rollback on failure
                self._conn.execute("SAVEPOINT populate_symbols_sp")

                # Count what we're about to delete (for logging)
                cur = self._conn.execute("""
                    SELECT COUNT(*) FROM symbols
                    WHERE provider = ?
                    AND provider_symbol NOT IN (SELECT provider_symbol FROM _incoming_symbols)
                """, (provider,))
                stale_count = cur.fetchone()[0]
                if stale_count:
                    logger.debug("removing %d stale symbols from provider=%s", stale_count, provider)

                # Delete rates for symbols being removed
                self._conn.execute("""
                    DELETE FROM rates WHERE symbol_id IN (
                        SELECT s.id FROM symbols s
                        WHERE s.provider = ?
                        AND s.provider_symbol NOT IN (SELECT provider_symbol FROM _incoming_symbols)
                    )
                """, (provider,))

                # Delete stale symbols
                self._conn.execute("""
                    DELETE FROM symbols
                    WHERE provider = ?
                    AND provider_symbol NOT IN (SELECT provider_symbol FROM _incoming_symbols)
                """, (provider,))

                # Update existing symbols
                self._conn.execute("""
                    UPDATE symbols SET
                        symbol = (SELECT symbol FROM _incoming_symbols WHERE provider_symbol = symbols.provider_symbol),
                        type = (SELECT type FROM _incoming_symbols WHERE provider_symbol = symbols.provider_symbol),
                        name = (SELECT name FROM _incoming_symbols WHERE provider_symbol = symbols.provider_symbol)
                    WHERE provider = ?
                    AND provider_symbol IN (SELECT provider_symbol FROM _incoming_symbols)
                """, (provider,))

                # Insert new symbols (those not already in main table for this provider)
                self._conn.execute("""
                    INSERT INTO symbols (provider, symbol, provider_symbol, type, name)
                    SELECT ?, i.symbol, i.provider_symbol, i.type, i.name
                    FROM _incoming_symbols i
                    WHERE NOT EXISTS (
                        SELECT 1 FROM symbols s
                        WHERE s.provider = ? AND s.provider_symbol = i.provider_symbol
                    )
                """, (provider, provider))

                self._conn.execute("RELEASE populate_symbols_sp")
                logger.debug("populate_symbols completed for provider=%s", provider)

            except Exception:
                self._conn.execute("ROLLBACK TO populate_symbols_sp")
                self._conn.execute("RELEASE populate_symbols_sp")
                raise
            finally:
                # Clear temp table for next use
                self._conn.execute("DELETE FROM _incoming_symbols")

    def get_symbols_populated_at(self, provider: str) -> str | None:
        """Get ISO timestamp of when symbols were last populated for provider."""
        with self._lock:
            if self._closed:
                return None
            cur = self._conn.execute(
                "SELECT value FROM metadata WHERE key = ?",
                (f"symbols_populated:{provider}",),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def set_symbols_populated_at(self, provider: str, timestamp: str) -> None:
        """Set ISO timestamp of when symbols were populated for provider."""
        with self._lock:
            if self._closed:
                return
            self._conn.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                (f"symbols_populated:{provider}", timestamp),
            )

    def get_backfill_done_at(self, provider: str) -> str | None:
        """Get ISO timestamp of when backfill was last done for provider."""
        with self._lock:
            if self._closed:
                return None
            cur = self._conn.execute(
                "SELECT value FROM metadata WHERE key = ?",
                (f"backfill_done:{provider}",),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def set_backfill_done_at(self, provider: str, timestamp: str) -> None:
        """Set ISO timestamp of when backfill was done for provider."""
        with self._lock:
            if self._closed:
                return
            self._conn.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                (f"backfill_done:{provider}", timestamp),
            )

    def get_backfill_checkpoint(self, provider: str) -> dict | None:
        """Get backfill checkpoint for provider.

        Returns dict with last_symbol_idx, length, timestamp or None.
        """
        import json
        with self._lock:
            if self._closed:
                return None
            cur = self._conn.execute(
                "SELECT value FROM metadata WHERE key = ?",
                (f"backfill_checkpoint:{provider}",),
            )
            row = cur.fetchone()
            if not row:
                return None
            try:
                return json.loads(row[0])
            except (json.JSONDecodeError, TypeError):
                return None

    def set_backfill_checkpoint(self, provider: str, checkpoint: dict) -> None:
        """Save backfill checkpoint for provider."""
        import json
        with self._lock:
            if self._closed:
                return
            self._conn.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                (f"backfill_checkpoint:{provider}", json.dumps(checkpoint)),
            )

    def clear_backfill_checkpoint(self, provider: str) -> None:
        """Clear backfill checkpoint on completion."""
        with self._lock:
            if self._closed:
                return
            self._conn.execute(
                "DELETE FROM metadata WHERE key = ?",
                (f"backfill_checkpoint:{provider}",),
            )

    def count_symbols(self, provider: str) -> int:
        """Count symbols for a provider."""
        with self._lock:
            if self._closed:
                return 0
            cur = self._conn.execute(
                "SELECT COUNT(*) FROM symbols WHERE provider = ?",
                (provider,),
            )
            return cur.fetchone()[0]

    def count_symbols_by_type(self, provider: str) -> dict[str, int]:
        """Count symbols by type for a provider."""
        with self._lock:
            if self._closed:
                return {}
            cur = self._conn.execute(
                "SELECT type, COUNT(*) FROM symbols WHERE provider = ? GROUP BY type",
                (provider,),
            )
            return {row[0]: row[1] for row in cur.fetchall()}

    def upsert_symbols(self, provider: str, symbols: list[Symbol]) -> None:
        """Add or update symbols without deleting existing ones."""
        with self._lock:
            if self._closed:
                return

            for s in symbols:
                self._conn.execute(
                    """
                    INSERT INTO symbols (provider, symbol, provider_symbol, type, name)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(provider, provider_symbol) DO UPDATE SET
                        symbol = excluded.symbol,
                        type = excluded.type,
                        name = excluded.name
                    """,
                    (provider, s.symbol, s.provider_symbol, s.type, s.name),
                )

    def export_rates(self) -> list[dict]:
        """Export rates denormalized (includes provider_symbol and provider, not symbol_id)."""
        with self._lock:
            if self._closed:
                return []
            cur = self._conn.execute("""
                SELECT r.date, s.provider, s.provider_symbol, r.rate
                FROM rates r
                JOIN symbols s ON r.symbol_id = s.id
            """)
            return [
                {"date": row[0], "provider": row[1], "provider_symbol": row[2], "rate": row[3]}
                for row in cur.fetchall()
            ]

    def export_symbols(self) -> list[dict]:
        with self._lock:
            if self._closed:
                return []
            cur = self._conn.execute(
                "SELECT provider, symbol, provider_symbol, type, name FROM symbols"
            )
            return [
                {"provider": row[0], "symbol": row[1], "provider_symbol": row[2], "type": row[3], "name": row[4]}
                for row in cur.fetchall()
            ]

    def export_metadata(self) -> list[dict]:
        """Export metadata entries (excluding schema_version)."""
        with self._lock:
            if self._closed:
                return []
            cur = self._conn.execute(
                "SELECT key, value FROM metadata WHERE key != 'schema_version'"
            )
            return [{"key": row[0], "value": row[1]} for row in cur.fetchall()]

    def list_favorites(self) -> list[dict]:
        """Return favorite symbols ordered by newest addition."""
        with self._lock:
            if self._closed:
                return []
            cur = self._conn.execute("""
                SELECT s.provider, s.provider_symbol
                FROM favorites f
                JOIN symbols s ON f.symbol_id = s.id
                ORDER BY f.created_at DESC
            """)
            return [{"provider": row[0], "provider_symbol": row[1]} for row in cur.fetchall()]

    def export_favorites(self) -> list[dict]:
        """Export favorites with creation timestamps (denormalized for portability)."""
        with self._lock:
            if self._closed:
                return []
            cur = self._conn.execute("""
                SELECT s.provider, s.provider_symbol, f.created_at
                FROM favorites f
                JOIN symbols s ON f.symbol_id = s.id
                ORDER BY f.created_at DESC
            """)
            return [{"provider": row[0], "provider_symbol": row[1], "created_at": row[2]} for row in cur.fetchall()]

    def import_favorites(self, rows: list[dict]) -> int:
        """Import favorites, replacing existing. Looks up symbol_id from provider/provider_symbol."""
        with self._lock:
            if self._closed:
                return 0
            self._conn.execute("DELETE FROM favorites")
            if not rows:
                return 0
            count = 0
            for row in rows:
                if "provider" in row and "provider_symbol" in row:
                    cur = self._conn.execute(
                        "SELECT id FROM symbols WHERE provider = ? AND provider_symbol = ?",
                        (row["provider"], row["provider_symbol"]),
                    )
                    symbol_row = cur.fetchone()
                    if symbol_row:
                        self._conn.execute(
                            "INSERT OR IGNORE INTO favorites (symbol_id, created_at) VALUES (?, ?)",
                            (symbol_row[0], row.get("created_at")),
                        )
                        count += 1
            return count

    def add_favorite(self, provider: str, provider_symbol: str) -> bool:
        """Add a symbol to favorites. Returns True if added, False if symbol not found."""
        with self._lock:
            if self._closed:
                return False
            cur = self._conn.execute(
                "SELECT id FROM symbols WHERE provider = ? AND provider_symbol = ?",
                (provider, provider_symbol),
            )
            row = cur.fetchone()
            if not row:
                logger.warning("add_favorite: symbol not found provider=%s provider_symbol=%s", provider, provider_symbol)
                return False
            self._conn.execute(
                "INSERT OR IGNORE INTO favorites (symbol_id) VALUES (?)",
                (row[0],),
            )
            return True

    def remove_favorite(self, provider: str, provider_symbol: str) -> bool:
        """Remove a symbol from favorites. Returns True if removed, False if symbol not found."""
        with self._lock:
            if self._closed:
                return False
            cur = self._conn.execute(
                "SELECT id FROM symbols WHERE provider = ? AND provider_symbol = ?",
                (provider, provider_symbol),
            )
            row = cur.fetchone()
            if not row:
                return False
            self._conn.execute(
                "DELETE FROM favorites WHERE symbol_id = ?",
                (row[0],),
            )
            return True

    def import_rates(self, rows: list[dict]) -> int:
        with self._lock:
            if self._closed:
                return 0
            try:
                self._conn.execute("BEGIN")
                self._conn.execute("DELETE FROM rates")
                if not rows:
                    self._conn.execute("COMMIT")
                    return 0

                count = 0
                for row in rows:
                    # Support both old format (symbol) and new format (provider_symbol)
                    provider_symbol = row.get("provider_symbol") or row.get("symbol")
                    cur = self._conn.execute(
                        "SELECT id FROM symbols WHERE provider = ? AND provider_symbol = ?",
                        (row["provider"], provider_symbol),
                    )
                    symbol_row = cur.fetchone()
                    if not symbol_row:
                        continue

                    self._conn.execute(
                        "INSERT INTO rates (date, symbol_id, rate) VALUES (?, ?, ?)",
                        (row["date"], symbol_row[0], row["rate"]),
                    )
                    count += 1

                self._conn.execute("COMMIT")
                return count
            except Exception:
                self._conn.execute("ROLLBACK")
                raise

    def import_symbols(self, rows: list[dict]) -> int:
        with self._lock:
            if self._closed:
                return 0
            try:
                self._conn.execute("BEGIN")
                self._conn.execute("DELETE FROM rates")
                self._conn.execute("DELETE FROM symbols")
                if not rows:
                    self._conn.execute("COMMIT")
                    return 0

                for row in rows:
                    # Support both old format and new format
                    if "provider_symbol" in row:
                        # New format
                        symbol = row["symbol"]
                        provider_symbol = row["provider_symbol"]
                    else:
                        # Old format: symbol was provider_symbol, normalized_symbol was symbol
                        provider_symbol = row["symbol"]
                        symbol = row.get("normalized_symbol") or row["symbol"]
                    self._conn.execute(
                        "INSERT INTO symbols (provider, symbol, provider_symbol, type, name) VALUES (?, ?, ?, ?, ?)",
                        (row["provider"], symbol, provider_symbol, row["type"], row.get("name")),
                    )
                self._conn.execute("COMMIT")
                return len(rows)
            except Exception:
                self._conn.execute("ROLLBACK")
                raise

    def import_metadata(self, rows: list[dict]) -> int:
        """Import metadata entries (excluding schema_version)."""
        with self._lock:
            if self._closed:
                return 0
            # Clear existing non-schema metadata
            self._conn.execute("DELETE FROM metadata WHERE key != 'schema_version'")
            if not rows:
                return 0
            for row in rows:
                if row["key"] != "schema_version":
                    self._conn.execute(
                        "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                        (row["key"], row["value"]),
                    )
            return len([r for r in rows if r["key"] != "schema_version"])

    def commit(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._conn.commit()
            self._conn.close()
