from data.schemas import (
    CompanyEnrichmentResponse,
    CompanySearchResponse,
    DecisionMakersResponse,
    FundingMilestoneTimeseriesResponse,
    HeadcountTimeseriesResponse,
    InvestorPortfolioResponse,
    LinkedInPostsResponse,
    PersonScreenerResponse,
)
from scoring.schemas import Criterion, CriterionScore


def score_capability_match(
    search_results: CompanySearchResponse,
    enrichment: CompanyEnrichmentResponse,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore:
    """How closely candidate companies' tech/product matches the target capability.

    Source: company_search + company_enrichment.technographics.
    Scale: 0-10.
    """
    raise NotImplementedError


def score_acquirable_size(
    headcount: HeadcountTimeseriesResponse,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore:
    """Headcount/scale bucket suggesting the company is small enough to absorb.

    Source: headcount_timeseries.
    Scale: 0-10, 10 = ideal acquirable size (5-50 employees), 0 = too large or pre-product.
    """
    raise NotImplementedError


def score_acquirable_funding_stage(
    funding_milestones: FundingMilestoneTimeseriesResponse,
    investor_portfolio: InvestorPortfolioResponse,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore:
    """Funding trajectory suggesting openness to acquisition.

    Source: funding_milestone_timeseries + investor_portfolio_data.
    Scale: 0-10, 10 = classic acquirable profile.
    """
    raise NotImplementedError


def score_team_quality_signal(
    persons: PersonScreenerResponse,
    linkedin_posts: LinkedInPostsResponse,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore:
    """Signals of a strong core team worth acquiring, not just the product.

    Source: person_screener + linkedin_posts (founder/team activity).
    Scale: 0-10.
    """
    raise NotImplementedError


def score_decision_maker_reachability(
    decision_makers: DecisionMakersResponse,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore:
    """Named founders/execs to open acquisition conversations with.

    Source: decision_makers_filter / person_screener.
    Scale: 0-10.
    """
    raise NotImplementedError
