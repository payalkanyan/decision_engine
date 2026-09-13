import json
from pathlib import Path

import pytest

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

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a JSON fixture file as a dict."""
    return json.loads((FIXTURES_DIR / name).read_text())


@pytest.fixture
def company_enrichment() -> CompanyEnrichmentResponse:
    return CompanyEnrichmentResponse.model_validate(load_fixture("company_enrichment.json"))


@pytest.fixture
def company_search() -> CompanySearchResponse:
    return CompanySearchResponse.model_validate(load_fixture("company_search.json"))


@pytest.fixture
def jobs() -> JobsResponse:
    return JobsResponse.model_validate(load_fixture("jobs.json"))


@pytest.fixture
def headcount_timeseries() -> HeadcountTimeseriesResponse:
    return HeadcountTimeseriesResponse.model_validate(load_fixture("headcount_timeseries.json"))


@pytest.fixture
def funding_milestones() -> FundingMilestoneTimeseriesResponse:
    return FundingMilestoneTimeseriesResponse.model_validate(
        load_fixture("funding_milestones.json")
    )


@pytest.fixture
def decision_makers() -> DecisionMakersResponse:
    return DecisionMakersResponse.model_validate(load_fixture("decision_makers.json"))


@pytest.fixture
def person_screener() -> PersonScreenerResponse:
    return PersonScreenerResponse.model_validate(load_fixture("person_screener.json"))


@pytest.fixture
def investor_portfolio() -> InvestorPortfolioResponse:
    return InvestorPortfolioResponse.model_validate(load_fixture("investor_portfolio.json"))


@pytest.fixture
def linkedin_posts() -> LinkedInPostsResponse:
    return LinkedInPostsResponse.model_validate(load_fixture("linkedin_posts.json"))


@pytest.fixture
def web_traffic() -> WebTrafficResponse:
    return WebTrafficResponse.model_validate(load_fixture("web_traffic.json"))
