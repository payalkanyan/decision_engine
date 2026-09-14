"""Tests for data/caching_client.py — the cache-first Crustdata client."""

import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx
from pydantic import ValidationError

from data.caching_client import (
    ENDPOINT_TTLS,
    ERROR_TTL,
    ApiProvenanceRecord,
    CachingClient,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
BASE_URL = "https://api.crustdata.com"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


@pytest.fixture(autouse=True)
def _api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CRUSTDATA_API_KEY", "test-api-key")


@pytest.fixture
def tmp_cache(tmp_path: Path) -> CachingClient:
    return CachingClient(api_key="test-api-key", cache_db=str(tmp_path / "cache.db"))


# ── 1. Cache hit/miss behavior ─────────────────────────────────────


@respx.mock
def test_first_call_hits_api_second_call_hits_cache(tmp_cache: CachingClient) -> None:
    route = respx.post(f"{BASE_URL}/company/enrich").mock(
        return_value=httpx.Response(200, json=load_fixture("company_enrichment.json")),
    )

    # First call: cache miss
    model1, prov1 = tmp_cache.get_company_enrichment("TechCorp")
    assert route.call_count == 1
    assert prov1.cache_hit is False
    assert model1.company.company_name == "TechCorp Inc"

    # Second call: cache hit
    model2, prov2 = tmp_cache.get_company_enrichment("TechCorp")
    assert route.call_count == 1  # no additional API call
    assert prov2.cache_hit is True
    assert model2.company.company_name == "TechCorp Inc"

    # Timestamps should differ
    assert prov1.timestamp != prov2.timestamp


# ── 2. Per-endpoint TTL verification ────────────────────────────────


def test_per_endpoint_ttls_are_configured() -> None:
    """Spot-check TTL values for three representative endpoints."""
    assert ENDPOINT_TTLS["company_enrichment"] == 86400  # 24h
    assert ENDPOINT_TTLS["jobs"] == 3600  # 1h
    assert ENDPOINT_TTLS["headcount_timeseries"] == 604800  # 7d


def test_error_ttl_is_shorter_than_all_endpoint_ttls() -> None:
    """5xx error TTL should be shorter than any endpoint TTL."""
    assert ERROR_TTL == 300  # 5 minutes
    for endpoint, ttl in ENDPOINT_TTLS.items():
        assert ttl > ERROR_TTL, f"ERROR_TTL should be shorter than {endpoint} TTL"


# ── 3. Error handling ──────────────────────────────────────────────


@respx.mock
def test_5xx_error_is_cached_and_raises_validation_on_retry(tmp_cache: CachingClient) -> None:
    """5xx errors are cached with short TTL; retry hits cache and fails validation."""
    route = respx.post(f"{BASE_URL}/company/enrich").mock(
        return_value=httpx.Response(502),
    )

    # First call: 502 error, gets cached. Client retries 3 times before raising.
    with patch("data.client.time.sleep"), pytest.raises(httpx.HTTPStatusError):
        tmp_cache.get_company_enrichment("TechCorp")
    assert route.call_count == 3  # MAX_RETRIES in data/client.py

    # Second call: hits cached error marker, raises ValidationError (not HTTPStatusError)
    # Cached 5xx error marker causes validation failure on retry, preventing API hammering
    with pytest.raises(ValidationError):
        tmp_cache.get_company_enrichment("TechCorp")
    assert route.call_count == 3  # no additional API call — served from cache


@respx.mock
def test_4xx_error_is_not_cached(tmp_cache: CachingClient) -> None:
    """4xx errors are NOT cached; each call hits the API."""
    route = respx.post(f"{BASE_URL}/company/enrich").mock(
        return_value=httpx.Response(404),
    )

    # First call: 404 error
    with pytest.raises(httpx.HTTPStatusError):
        tmp_cache.get_company_enrichment("TechCorp")
    assert route.call_count == 1

    # Second call: should hit API again (not cached)
    with pytest.raises(httpx.HTTPStatusError):
        tmp_cache.get_company_enrichment("TechCorp")
    assert route.call_count == 2


# ── 4. All 10 endpoint methods ────────────────────────────────------

# NOTE: Cache-hit branches for endpoints other than company_enrichment (lines 178,
# 197, 202, 219, 224, 244, 264, 284, 304, 324, 344) are not individually tested.
# The hit/miss code path is identical across all endpoints — only the pydantic
# model differs — and is exercised via test_first_call_hits_api_second_call_hits_cache.
# Adding 9 redundant cache-hit tests would be pure duplication.


@respx.mock
def test_all_endpoints_return_model_with_cache_hit_false(tmp_cache: CachingClient) -> None:
    """Each endpoint returns (model, cache_hit=False) on first call."""
    # Register all mock routes
    respx.post(f"{BASE_URL}/company/enrich").mock(
        return_value=httpx.Response(200, json=load_fixture("company_enrichment.json")),
    )
    respx.post(f"{BASE_URL}/company/search").mock(
        return_value=httpx.Response(200, json=load_fixture("company_search.json")),
    )
    respx.get(f"{BASE_URL}/jobs").mock(
        return_value=httpx.Response(200, json=load_fixture("jobs.json")),
    )
    respx.get(f"{BASE_URL}/company/headcount").mock(
        return_value=httpx.Response(200, json=load_fixture("headcount_timeseries.json")),
    )
    respx.get(f"{BASE_URL}/company/funding").mock(
        return_value=httpx.Response(200, json=load_fixture("funding_milestones.json")),
    )
    respx.get(f"{BASE_URL}/company/decision-makers").mock(
        return_value=httpx.Response(200, json=load_fixture("decision_makers.json")),
    )
    respx.post(f"{BASE_URL}/persons/screener").mock(
        return_value=httpx.Response(200, json=load_fixture("person_screener.json")),
    )
    respx.get(f"{BASE_URL}/investors/portfolio").mock(
        return_value=httpx.Response(200, json=load_fixture("investor_portfolio.json")),
    )
    respx.get(f"{BASE_URL}/company/linkedin-posts").mock(
        return_value=httpx.Response(200, json=load_fixture("linkedin_posts.json")),
    )
    respx.get(f"{BASE_URL}/web/traffic").mock(
        return_value=httpx.Response(200, json=load_fixture("web_traffic.json")),
    )

    # Call each endpoint and verify cache_hit=False
    endpoints_and_calls = [
        lambda: tmp_cache.get_company_enrichment("TechCorp"),
        lambda: tmp_cache.search_companies({"industry": "AI/ML"}),
        lambda: tmp_cache.get_jobs(company_name="TechCorp"),
        lambda: tmp_cache.get_headcount_timeseries("TechCorp"),
        lambda: tmp_cache.get_funding_milestones("TechCorp"),
        lambda: tmp_cache.get_decision_makers("TechCorp"),
        lambda: tmp_cache.screen_persons({"title": "CEO"}),
        lambda: tmp_cache.get_investor_portfolio("Sequoia"),
        lambda: tmp_cache.get_linkedin_posts("TechCorp"),
        lambda: tmp_cache.get_web_traffic("techcorp.com"),
    ]

    for call_fn in endpoints_and_calls:
        model, provenance = call_fn()
        assert provenance.cache_hit is False
        assert model is not None


# ── 5. Provenance correctness ──────────────────────────────────────


@respx.mock
def test_provenance_has_unique_api_call_id(tmp_cache: CachingClient) -> None:
    respx.post(f"{BASE_URL}/company/enrich").mock(
        return_value=httpx.Response(200, json=load_fixture("company_enrichment.json")),
    )

    _, prov1 = tmp_cache.get_company_enrichment("TechCorp")
    _, prov2 = tmp_cache.get_company_enrichment("TechCorp")

    # Each call gets a unique UUID
    assert prov1.api_call_id != prov2.api_call_id
    # Valid UUID format
    assert len(prov1.api_call_id) == 36


@respx.mock
def test_provenance_timestamp_is_recent(tmp_cache: CachingClient) -> None:
    from datetime import UTC, datetime

    respx.post(f"{BASE_URL}/company/enrich").mock(
        return_value=httpx.Response(200, json=load_fixture("company_enrichment.json")),
    )

    before = datetime.now(UTC)
    _, prov = tmp_cache.get_company_enrichment("TechCorp")
    after = datetime.now(UTC)

    assert before <= prov.timestamp <= after


@respx.mock
def test_provenance_cache_hit_matches_state(tmp_cache: CachingClient) -> None:
    respx.post(f"{BASE_URL}/company/enrich").mock(
        return_value=httpx.Response(200, json=load_fixture("company_enrichment.json")),
    )

    _, prov1 = tmp_cache.get_company_enrichment("TechCorp")
    _, prov2 = tmp_cache.get_company_enrichment("TechCorp")

    assert prov1.cache_hit is False
    assert prov2.cache_hit is True


@respx.mock
def test_provenance_request_fields_matches_params(tmp_cache: CachingClient) -> None:
    respx.post(f"{BASE_URL}/company/enrich").mock(
        return_value=httpx.Response(200, json=load_fixture("company_enrichment.json")),
    )

    _, prov = tmp_cache.get_company_enrichment("TechCorp")
    assert prov.request_fields == ["name=TechCorp"]

    # Different params → different request_fields
    _, prov2 = tmp_cache.get_company_enrichment("OtherCorp")
    assert prov2.request_fields == ["name=OtherCorp"]


@respx.mock
def test_api_provenance_record_is_pydantic_model() -> None:
    """ApiProvenanceRecord should be a proper pydantic model."""
    from datetime import UTC, datetime

    record = ApiProvenanceRecord(
        api_call_id="test-uuid",
        timestamp=datetime.now(UTC),
        cache_hit=False,
        request_fields=["name=TechCorp"],
    )
    assert isinstance(record, ApiProvenanceRecord)
    assert record.api_call_id == "test-uuid"
