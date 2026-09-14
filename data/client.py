import os
import time
from contextlib import suppress
from datetime import date

import httpx

from data.schemas import (
    CompanyEnrichment,
    CompanyEnrichmentResponse,
    CompanySearchResponse,
    DecisionMakersResponse,
    FundingMilestoneTimeseriesResponse,
    FundingSummary,
    HeadcountTimeseriesResponse,
    InvestorPortfolioResponse,
    JobsResponse,
    LinkedInPostsResponse,
    PersonScreenerResponse,
    Technographics,
    WebTrafficResponse,
)

MAX_RETRIES = 3
RETRY_BASE_SECONDS = 1.0
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


class CrustdataClient:
    """Raw HTTP client for the Crustdata API.

    One method per endpoint. Reads CRUSTDATA_API_KEY from the environment.
    Retries with exponential backoff on 429/5xx and transport errors.
    Parses responses into the pydantic models from data/schemas.py.

    This file has ZERO caching logic — it only knows how to make one HTTP
    call per method. All caching belongs in caching_client.py.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.crustdata.com",
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key or os.environ["CRUSTDATA_API_KEY"]
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Accept": "application/json",
                "x-api-version": "2025-11-01",
            },
            timeout=timeout,
        )

    def __enter__(self) -> "CrustdataClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self._client.close()

    def close(self) -> None:
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
    ) -> dict:
        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.request(
                    method, path, params=params, json=json_body
                )
            except httpx.TransportError:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BASE_SECONDS * (2 ** attempt))
                    continue
                raise

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_SECONDS * (2 ** attempt)
                if response.status_code == 429:
                    retry_after = response.headers.get("retry-after")
                    if retry_after:
                        with suppress(ValueError):
                            delay = float(retry_after)
                time.sleep(delay)
                continue

            response.raise_for_status()
            return response.json()

        # Unreachable, but keeps type checkers happy.
        raise httpx.HTTPStatusError(
            "request failed after retries",
            request=httpx.Request(method, path),
            response=httpx.Response(500),
        )

    def get_company_enrichment(self, company_name: str) -> CompanyEnrichmentResponse:
        """Fetch company enrichment via POST /company/enrich (API v2).

        The response is an array of EnrichResult objects. We take the
        highest-confidence match and map it onto the legacy CompanyEnrichment
        schema so scoring criteria stay unchanged.
        """
        data = self._request(
            "POST",
            "/company/enrich",
            json_body={
                "names": [company_name],
                "fields": ["basic_info", "headcount", "funding", "taxonomy"],
            },
        )

        if not data or not isinstance(data, list) or not data[0].get("matches"):
            return CompanyEnrichmentResponse(
                company=CompanyEnrichment(company_name=company_name)
            )

        best = max(data[0]["matches"], key=lambda m: m.get("confidence_score", 0))
        cd = best.get("company_data", {})
        basic = cd.get("basic_info") or {}
        funding = cd.get("funding") or {}
        headcount = cd.get("headcount") or {}
        taxonomy = cd.get("taxonomy") or {}

        # technographics isn't available on this API key tier, so we map
        # taxonomy categories and industries into the Technographics schema
        # slots the scoring criteria read from.
        categories = taxonomy.get("categories") or basic.get("industries") or []
        technologies = taxonomy.get("professional_network_industries") or []

        return CompanyEnrichmentResponse(
            company=CompanyEnrichment(
                company_name=basic.get("name") or company_name,
                domain=basic.get("primary_domain"),
                industry=basic.get("industries", [None])[0]
                if basic.get("industries")
                else None,
                description=basic.get("description"),
                employee_count=headcount.get("total"),
                founded_date=date(basic["year_founded"], 1, 1)
                if basic.get("year_founded")
                else None,
                location=basic.get("headquarters") or basic.get("country"),
                technographics=Technographics(
                    technologies=technologies,
                    categories=categories,
                ),
                funding=FundingSummary(
                    total_raised=funding.get("total_investment_usd"),
                    latest_round_type=funding.get("last_round_type"),
                    latest_round_amount=funding.get("last_round_amount_usd"),
                    latest_round_date=funding.get("last_fundraise_date"),
                ),
            )
        )

    def search_companies(self, filters: dict) -> CompanySearchResponse:
        data = self._request("POST", "/company/search", json_body=filters)
        return CompanySearchResponse.model_validate(data)

    def get_jobs(
        self, company_name: str | None = None, filters: dict | None = None
    ) -> JobsResponse:
        params: dict = {}
        if company_name:
            params["company"] = company_name
        if filters:
            params.update(filters)
        data = self._request("GET", "/jobs", params=params or None)
        return JobsResponse.model_validate(data)

    def get_headcount_timeseries(
        self, company_name: str, facet: str | None = None
    ) -> HeadcountTimeseriesResponse:
        params = {"company": company_name}
        if facet:
            params["facet"] = facet
        data = self._request("GET", "/company/headcount", params=params)
        return HeadcountTimeseriesResponse.model_validate(data)

    def get_funding_milestones(self, company_name: str) -> FundingMilestoneTimeseriesResponse:
        data = self._request("GET", "/company/funding", params={"company": company_name})
        return FundingMilestoneTimeseriesResponse.model_validate(data)

    def get_decision_makers(self, company_name: str) -> DecisionMakersResponse:
        data = self._request("GET", "/company/decision-makers", params={"company": company_name})
        return DecisionMakersResponse.model_validate(data)

    def screen_persons(self, filters: dict) -> PersonScreenerResponse:
        data = self._request("POST", "/persons/screener", json_body=filters)
        return PersonScreenerResponse.model_validate(data)

    def get_investor_portfolio(self, investor_name: str) -> InvestorPortfolioResponse:
        data = self._request("GET", "/investors/portfolio", params={"name": investor_name})
        return InvestorPortfolioResponse.model_validate(data)

    def get_linkedin_posts(self, company_name: str) -> LinkedInPostsResponse:
        data = self._request("GET", "/company/linkedin-posts", params={"company": company_name})
        return LinkedInPostsResponse.model_validate(data)

    def get_web_traffic(self, domain: str) -> WebTrafficResponse:
        data = self._request("GET", "/web/traffic", params={"domain": domain})
        return WebTrafficResponse.model_validate(data)
