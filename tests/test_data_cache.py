from datetime import UTC, datetime, timedelta
from pathlib import Path

from data.cache import ResponseCache


def _make_cache(tmp_path: Path, ttl: int = 86400) -> ResponseCache:
    return ResponseCache(db_path=str(tmp_path / "cache.db"), ttl_seconds=ttl)


def test_make_cache_key_is_deterministic() -> None:
    key1 = ResponseCache.make_cache_key("company_enrichment", {"name": "TechCorp"})
    key2 = ResponseCache.make_cache_key("company_enrichment", {"name": "TechCorp"})
    assert key1 == key2


def test_make_cache_key_is_order_independent() -> None:
    key1 = ResponseCache.make_cache_key("jobs", {"a": 1, "b": 2})
    key2 = ResponseCache.make_cache_key("jobs", {"b": 2, "a": 1})
    assert key1 == key2


def test_make_cache_key_differs_for_different_input() -> None:
    key1 = ResponseCache.make_cache_key("jobs", {"a": 1})
    key2 = ResponseCache.make_cache_key("jobs", {"a": 2})
    key3 = ResponseCache.make_cache_key("other", {"a": 1})
    assert key1 != key2
    assert key1 != key3


def test_set_then_get_returns_value(tmp_path: Path) -> None:
    cache = _make_cache(tmp_path)
    payload = {"company": {"company_name": "TechCorp", "employee_count": 250}}
    cache.set("key-1", payload)

    result = cache.get("key-1")
    assert result == payload


def test_get_missing_key_returns_none(tmp_path: Path) -> None:
    cache = _make_cache(tmp_path)
    assert cache.get("does-not-exist") is None


def test_has_returns_true_for_existing_key(tmp_path: Path) -> None:
    cache = _make_cache(tmp_path)
    cache.set("key-1", {"data": 1})
    assert cache.has("key-1") is True


def test_has_returns_false_for_missing_key(tmp_path: Path) -> None:
    cache = _make_cache(tmp_path)
    assert cache.has("does-not-exist") is False


def test_set_overwrites_existing_key(tmp_path: Path) -> None:
    cache = _make_cache(tmp_path)
    cache.set("key-1", {"v": 1})
    cache.set("key-1", {"v": 2})

    assert cache.get("key-1") == {"v": 2}


def test_get_returns_none_after_ttl_expiry(tmp_path: Path) -> None:
    cache = _make_cache(tmp_path, ttl=3600)
    cache.set("key-1", {"data": "stale"})

    # Manually backdate the row past the TTL
    old_ts = (datetime.now(UTC) - timedelta(seconds=7200)).isoformat()
    import sqlite3

    conn = sqlite3.connect(str(tmp_path / "cache.db"))
    conn.execute("UPDATE cache SET fetched_at = ? WHERE key = ?", (old_ts, "key-1"))
    conn.commit()
    conn.close()

    assert cache.get("key-1") is None
    assert cache.has("key-1") is False


def test_per_entry_ttl_overrides_instance_default(tmp_path: Path) -> None:
    # Instance TTL is long, but this entry uses a short override
    cache = _make_cache(tmp_path, ttl=86400)
    cache.set("short", {"data": "x"}, ttl_seconds=1)
    cache.set("long", {"data": "y"})

    import sqlite3

    conn = sqlite3.connect(str(tmp_path / "cache.db"))
    old_ts = (datetime.now(UTC) - timedelta(seconds=5)).isoformat()
    conn.execute("UPDATE cache SET fetched_at = ?", (old_ts,))
    conn.commit()
    conn.close()

    assert cache.get("short") is None  # expired via per-entry TTL
    assert cache.get("long") == {"data": "y"}  # still fresh via instance TTL
