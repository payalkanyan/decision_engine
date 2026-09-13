import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


class ResponseCache:
    """Thin SQLite-backed cache for JSON-serializable responses.

    Key = deterministic hash of (endpoint_name, request_params).
    Stores the raw JSON response plus a fetched_at timestamp.
    No Crustdata-specific knowledge — works for any JSON-serializable payload.

    Expired rows are skipped on read (treated as a miss) but not deleted —
    they are overwritten on the next set() for the same key, so they never
    accumulate without bound.
    """

    def __init__(
        self, db_path: str = ".cache/crustdata_cache.db", ttl_seconds: int = 86400
    ) -> None:
        self._db_path = Path(db_path)
        self._ttl_seconds = ttl_seconds
        self._ensure_table()

    def _ensure_table(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    ttl_seconds INTEGER NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def make_cache_key(endpoint: str, params: dict) -> str:
        """Deterministic SHA-256 hash of endpoint + sorted params."""
        raw = json.dumps({"endpoint": endpoint, "params": params}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, key: str) -> dict | None:
        """Return cached response if fresh (within TTL), else None.

        Expired rows are left in the table and treated as a miss; they get
        overwritten on the next set() for the same key.
        """
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT value, fetched_at, ttl_seconds FROM cache WHERE key = ?",
                (key,),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return None

        fetched_at = datetime.fromisoformat(row["fetched_at"])
        now = datetime.now(UTC)
        if fetched_at.tzinfo is None:
            # Defensive: guards against rows written by a future migration or
            # manual insert without tz info. set() always writes UTC-aware.
            fetched_at = fetched_at.replace(tzinfo=UTC)
        age_seconds = (now - fetched_at).total_seconds()

        effective_ttl = (
            row["ttl_seconds"] if row["ttl_seconds"] is not None else self._ttl_seconds
        )
        if age_seconds > effective_ttl:
            return None

        return json.loads(row["value"])

    def set(self, key: str, value: dict, ttl_seconds: int | None = None) -> None:
        """Store a response with a fetched_at timestamp.

        ttl_seconds overrides the instance default for this entry, allowing
        the caller (e.g. caching_client) to use a per-endpoint TTL without
        modifying this class.
        """
        effective_ttl = ttl_seconds if ttl_seconds is not None else self._ttl_seconds
        fetched_at = datetime.now(UTC).isoformat()
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache
                    (key, value, fetched_at, ttl_seconds)
                VALUES (?, ?, ?, ?)
                """,
                (key, json.dumps(value), fetched_at, effective_ttl),
            )
            conn.commit()
        finally:
            conn.close()

    def has(self, key: str) -> bool:
        """True if a fresh (unexpired) entry exists for key."""
        return self.get(key) is not None
