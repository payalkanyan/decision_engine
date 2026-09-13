from data.provenance import ProvenanceRecord
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


class CachingClient:
    """The facade: combines CrustdataClient + ResponseCache + provenance.

    This is the *only* module that scoring/LLM/CLI code import from /data.
    Returns typed schema objects + provenance records.
    """

    def __init__(
        self, api_key: str, cache_db: str = ".cache/crustdata_cache.db", ttl: int = 86400
    ) -> None:
        self._api_key = api_key
        self._cache_db = cache_db
        self._ttl = ttl

    def get_company_enrichment(self, company_name: str) -> tuple[CompanyEnrichmentResponse, str]:
        """Returns (typed response, api_call_id) — cache-first, provenance-stamped."""
        raise NotImplementedError

    def search_companies(self, filters: dict) -> tuple[CompanySearchResponse, str]:
        raise NotImplementedError

    def get_jobs(
        self, company_name: str | None = None, filters: dict | None = None
    ) -> tuple[JobsResponse, str]:
        raise NotImplementedError

    def get_headcount_timeseries(
        self, company_name: str, facet: str | None = None
    ) -> tuple[HeadcountTimeseriesResponse, str]:
        raise NotImplementedError

    def get_funding_milestones(
        self, company_name: str
    ) -> tuple[FundingMilestoneTimeseriesResponse, str]:
        raise NotImplementedError

    def get_decision_makers(self, company_name: str) -> tuple[DecisionMakersResponse, str]:
        raise NotImplementedError

    def screen_persons(self, filters: dict) -> tuple[PersonScreenerResponse, str]:
        raise NotImplementedError

    def get_investor_portfolio(self, investor_name: str) -> tuple[InvestorPortfolioResponse, str]:
        raise NotImplementedError

    def get_linkedin_posts(self, company_name: str) -> tuple[LinkedInPostsResponse, str]:
        raise NotImplementedError

    def get_web_traffic(self, domain: str) -> tuple[WebTrafficResponse, str]:
        raise NotImplementedError

    def make_provenance(
        self, criterion_id: str, raw_value: float, source_field: str, api_call_id: str
    ) -> ProvenanceRecord:
        """Build a provenance record for a given score."""
        raise NotImplementedError
