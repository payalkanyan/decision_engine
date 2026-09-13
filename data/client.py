import httpx

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


class CrustdataClient:
    """Thin HTTP client wrapping the Crustdata API.

    One method per endpoint. Handles auth headers, rate limits, retries.
    Never called directly by scoring or LLM code — use CachingClient instead.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.crustdata.com") -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._client: httpx.Client | None = None

    def get_company_enrichment(self, company_name: str) -> CompanyEnrichmentResponse:
        raise NotImplementedError

    def search_companies(self, filters: dict) -> CompanySearchResponse:
        raise NotImplementedError

    def get_jobs(
        self, company_name: str | None = None, filters: dict | None = None
    ) -> JobsResponse:
        raise NotImplementedError

    def get_headcount_timeseries(
        self, company_name: str, facet: str | None = None
    ) -> HeadcountTimeseriesResponse:
        raise NotImplementedError

    def get_funding_milestones(self, company_name: str) -> FundingMilestoneTimeseriesResponse:
        raise NotImplementedError

    def get_decision_makers(self, company_name: str) -> DecisionMakersResponse:
        raise NotImplementedError

    def screen_persons(self, filters: dict) -> PersonScreenerResponse:
        raise NotImplementedError

    def get_investor_portfolio(self, investor_name: str) -> InvestorPortfolioResponse:
        raise NotImplementedError

    def get_linkedin_posts(self, company_name: str) -> LinkedInPostsResponse:
        raise NotImplementedError

    def get_web_traffic(self, domain: str) -> WebTrafficResponse:
        raise NotImplementedError
