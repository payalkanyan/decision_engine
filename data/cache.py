import sqlite3
from pathlib import Path


class ResponseCache:
    """SQLite response cache for Crustdata API responses.

    Stores raw API responses by endpoint + params hash with a TTL.
    Every response is cached *before* scoring touches it.
    """

    def __init__(
        self, db_path: str = ".cache/crustdata_cache.db", ttl_seconds: int = 86400
    ) -> None:
        self._db_path = Path(db_path)
        self._ttl_seconds = ttl_seconds
        self._conn: sqlite3.Connection | None = None

    def get(self, cache_key: str) -> dict | None:
        """Return cached response if fresh, else None."""
        raise NotImplementedError

    def set(self, cache_key: str, response: dict, api_call_id: str) -> None:
        """Store a response with its provenance metadata."""
        raise NotImplementedError

    @staticmethod
    def make_cache_key(endpoint: str, params: dict) -> str:
        """Deterministic hash key from endpoint + sorted params."""
        raise NotImplementedError
