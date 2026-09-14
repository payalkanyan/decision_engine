"""Caching wrapper around CrustdataClient.

This is the ONE AND ONLY client the rest of the codebase imports.
data/client.py and data/cache.py are internal implementation details.

Every public method:
1. Checks cache first (via ResponseCache.get)
2. On miss, calls the raw CrustdataClient method
3. Writes the result to cache with a per-endpoint TTL
4. Returns (parsed_model, ApiProvenanceRecord)

5xx errors are cached with a short TTL to avoid hammering a struggling API.
4xx errors are not cached.
"""

import uuid
from datetime import UTC, datetime

import httpx
from pydantic import BaseModel

from data.cache import ResponseCache
from data.client import CrustdataClient
from data.schemas import (
    CompanyEnrichmentResponse,
    CompanySearchResponse,
    DecisionMakersResponse,
    FundingMilestoneTimeseriesResponse,
    HeadcountTimeseriesResponse,
    InvestorPortfolioResponse,
    JobsResponse,
    LinkedInPostsResponse,
    PersonScreenerResponse,
    WebTrafficResponse,
)

# Per-endpoint TTLs in seconds. Slower-moving data gets longer TTLs.
ENDPOINT_TTLS: dict[str, int] = {
    "company_enrichment": 86400,  # 24h
    "company_search": 3600,  # 1h
    "jobs": 3600,  # 1h
    "headcount_timeseries": 604800,  # 7d
    "funding_milestones": 604800,  # 7d
    "decision_makers": 86400,  # 24h
    "person_screener": 3600,  # 1h
    "investor_portfolio": 86400,  # 24h
    "linkedin_posts": 1800,  # 30m
    "web_traffic": 86400,  # 24h
}

ERROR_TTL = 300  # 5 minutes for 5xx responses


class ApiProvenanceRecord(BaseModel):
    """Provenance for a single cached API call.

    Attached to every response returned by CachingClient.
    """

    api_call_id: str
    timestamp: datetime
    cache_hit: bool
    request_fields: list[str]


class CachingClient:
    """Cache-first client wrapping CrustdataClient + ResponseCache.

    This is the single entry point for all Crustdata access in the codebase.
    Direct use of CrustdataClient or ResponseCache elsewhere is a layering
    violation.
    """

    def __init__(
        self,
        api_key: str | None = None,
        cache_db: str = ".cache/crustdata_cache.db",
        ttl: int = 86400,
    ) -> None:
        self._client = CrustdataClient(api_key=api_key) if api_key else CrustdataClient()
        self._cache = ResponseCache(db_path=cache_db, ttl_seconds=ttl)

    def _cache_key(self, endpoint: str, params: dict) -> str:
        return ResponseCache.make_cache_key(endpoint, params)

    def _check_cache(
        self,
        endpoint: str,
        params: dict,
        request_fields: list[str],
    ) -> tuple[dict | None, ApiProvenanceRecord]:
        """Check cache, return (data_or_none, provenance)."""
        key = self._cache_key(endpoint, params)
        timestamp = datetime.now(UTC)
        cached = self._cache.get(key)

        provenance = ApiProvenanceRecord(
            api_call_id=str(uuid.uuid4()),
            timestamp=timestamp,
            cache_hit=cached is not None,
            request_fields=request_fields,
        )
        return cached, provenance

    def _fetch(
        self,
        endpoint: str,
        params: dict,
        request_fields: list[str],
        fetch_fn,
    ):
        """Fetch from API, cache result, return (model, provenance).

        On 5xx errors, caches an error marker with a short TTL before
        re-raising. On 4xx errors, does not cache.
        """
        key = self._cache_key(endpoint, params)
        ttl = ENDPOINT_TTLS[endpoint]
        timestamp = datetime.now(UTC)

        try:
            result = fetch_fn()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status >= 500:
                self._cache.set(
                    key,
                    {"_error": True, "status_code": status},
                    ttl_seconds=ERROR_TTL,
                )
            raise

        self._cache.set(key, result.model_dump(mode="json"), ttl_seconds=ttl)

        provenance = ApiProvenanceRecord(
            api_call_id=str(uuid.uuid4()),
            timestamp=timestamp,
            cache_hit=False,
            request_fields=request_fields,
        )
        return result, provenance

    @staticmethod
    def _fields_from_params(params: dict) -> list[str]:
        return [f"{k}={v}" for k, v in params.items()]

    # ── Company Enrichment ─────────────────────────────────────────

    def get_company_enrichment(
        self, company_name: str
    ) -> tuple[CompanyEnrichmentResponse, ApiProvenanceRecord]:
        endpoint = "company_enrichment"
        params = {"name": company_name}
        fields = self._fields_from_params(params)

        cached, provenance = self._check_cache(endpoint, params, fields)
        if cached is not None:
            return CompanyEnrichmentResponse.model_validate(cached), provenance

        return self._fetch(
            endpoint,
            params,
            fields,
            lambda: self._client.get_company_enrichment(company_name),
        )

    # ── Company Search ─────────────────────────────────────────────

    def search_companies(
        self, filters: dict
    ) -> tuple[CompanySearchResponse, ApiProvenanceRecord]:
        endpoint = "company_search"
        params = {"filters": filters}
        fields = self._fields_from_params(params)

        cached, provenance = self._check_cache(endpoint, params, fields)
        if cached is not None:
            return CompanySearchResponse.model_validate(cached), provenance

        return self._fetch(
            endpoint,
            params,
            fields,
            lambda: self._client.search_companies(filters),
        )

    # ── Jobs API ───────────────────────────────────────────────────

    def get_jobs(
        self, company_name: str | None = None, filters: dict | None = None
    ) -> tuple[JobsResponse, ApiProvenanceRecord]:
        endpoint = "jobs"
        params: dict = {}
        if company_name:
            params["company"] = company_name
        if filters:
            params["filters"] = filters
        fields = self._fields_from_params(params)

        cached, provenance = self._check_cache(endpoint, params, fields)
        if cached is not None:
            return JobsResponse.model_validate(cached), provenance

        return self._fetch(
            endpoint,
            params,
            fields,
            lambda: self._client.get_jobs(company_name, filters),
        )

    # ── Headcount Timeseries ───────────────────────────────────────

    def get_headcount_timeseries(
        self, company_name: str, facet: str | None = None
    ) -> tuple[HeadcountTimeseriesResponse, ApiProvenanceRecord]:
        endpoint = "headcount_timeseries"
        params: dict = {"company": company_name}
        if facet:
            params["facet"] = facet
        fields = self._fields_from_params(params)

        cached, provenance = self._check_cache(endpoint, params, fields)
        if cached is not None:
            return HeadcountTimeseriesResponse.model_validate(cached), provenance

        return self._fetch(
            endpoint,
            params,
            fields,
            lambda: self._client.get_headcount_timeseries(company_name, facet),
        )

    # ── Funding Milestone Timeseries ───────────────────────────────

    def get_funding_milestones(
        self, company_name: str
    ) -> tuple[FundingMilestoneTimeseriesResponse, ApiProvenanceRecord]:
        endpoint = "funding_milestones"
        params = {"company": company_name}
        fields = self._fields_from_params(params)

        cached, provenance = self._check_cache(endpoint, params, fields)
        if cached is not None:
            return FundingMilestoneTimeseriesResponse.model_validate(cached), provenance

        return self._fetch(
            endpoint,
            params,
            fields,
            lambda: self._client.get_funding_milestones(company_name),
        )

    # ── Decision Makers ────────────────────────────────────────────

    def get_decision_makers(
        self, company_name: str
    ) -> tuple[DecisionMakersResponse, ApiProvenanceRecord]:
        endpoint = "decision_makers"
        params = {"company": company_name}
        fields = self._fields_from_params(params)

        cached, provenance = self._check_cache(endpoint, params, fields)
        if cached is not None:
            return DecisionMakersResponse.model_validate(cached), provenance

        return self._fetch(
            endpoint,
            params,
            fields,
            lambda: self._client.get_decision_makers(company_name),
        )

    # ── Person Screener ────────────────────────────────────────────

    def screen_persons(
        self, filters: dict
    ) -> tuple[PersonScreenerResponse, ApiProvenanceRecord]:
        endpoint = "person_screener"
        params = {"filters": filters}
        fields = self._fields_from_params(params)

        cached, provenance = self._check_cache(endpoint, params, fields)
        if cached is not None:
            return PersonScreenerResponse.model_validate(cached), provenance

        return self._fetch(
            endpoint,
            params,
            fields,
            lambda: self._client.screen_persons(filters),
        )

    # ── Investor Portfolio ─────────────────────────────────────────

    def get_investor_portfolio(
        self, investor_name: str
    ) -> tuple[InvestorPortfolioResponse, ApiProvenanceRecord]:
        endpoint = "investor_portfolio"
        params = {"name": investor_name}
        fields = self._fields_from_params(params)

        cached, provenance = self._check_cache(endpoint, params, fields)
        if cached is not None:
            return InvestorPortfolioResponse.model_validate(cached), provenance

        return self._fetch(
            endpoint,
            params,
            fields,
            lambda: self._client.get_investor_portfolio(investor_name),
        )

    # ── LinkedIn Posts ─────────────────────────────────────────────

    def get_linkedin_posts(
        self, company_name: str
    ) -> tuple[LinkedInPostsResponse, ApiProvenanceRecord]:
        endpoint = "linkedin_posts"
        params = {"company": company_name}
        fields = self._fields_from_params(params)

        cached, provenance = self._check_cache(endpoint, params, fields)
        if cached is not None:
            return LinkedInPostsResponse.model_validate(cached), provenance

        return self._fetch(
            endpoint,
            params,
            fields,
            lambda: self._client.get_linkedin_posts(company_name),
        )

    # ── Web Traffic ────────────────────────────────────────────────

    def get_web_traffic(
        self, domain: str
    ) -> tuple[WebTrafficResponse, ApiProvenanceRecord]:
        endpoint = "web_traffic"
        params = {"domain": domain}
        fields = self._fields_from_params(params)

        cached, provenance = self._check_cache(endpoint, params, fields)
        if cached is not None:
            return WebTrafficResponse.model_validate(cached), provenance

        return self._fetch(
            endpoint,
            params,
            fields,
            lambda: self._client.get_web_traffic(domain),
        )
