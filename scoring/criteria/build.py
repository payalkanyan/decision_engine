from data.schemas import (
    CompanyEnrichmentResponse,
    CompanySearchResponse,
    FundingMilestoneTimeseriesResponse,
    HeadcountTimeseriesResponse,
    JobsResponse,
    PersonScreenerResponse,
)
from scoring.schemas import Criterion, CriterionScore


def score_internal_hiring_velocity(
    jobs: JobsResponse,
    headcount: HeadcountTimeseriesResponse,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore:
    """Rate at which the company is already hiring for adjacent roles.

    Source: jobs_api + headcount_timeseries (own company).
    Scale: 0-10, 10 = strong existing hiring motion.
    """
    raise NotImplementedError


def score_existing_tech_stack_overlap(
    enrichment: CompanyEnrichmentResponse,
    taxonomy_tags: list[str],
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore:
    """Overlap between company's current tech stack and capability requirements.

    Source: company_enrichment.technographics (own company).
    Scale: 0-10, 10 = capability is a natural extension of current stack.
    """
    raise NotImplementedError


def score_talent_market_availability(
    market_jobs: JobsResponse,
    persons: PersonScreenerResponse,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore:
    """Depth of hireable talent pool for this capability in relevant markets.

    Source: jobs_api (market-wide) + person_screener.
    Scale: 0-10, 10 = deep, liquid talent market.
    """
    raise NotImplementedError


def score_estimated_time_to_capability(
    hiring_velocity_score: CriterionScore,
    talent_availability_score: CriterionScore,
    criterion: Criterion,
) -> CriterionScore:
    """Estimated months to reach competitive capability internally.

    Source: derived from internal_hiring_velocity + talent_market_availability.
    Scale: 0-10, 10 = fast (<6 months), 0 = slow (>24 months).
    """
    raise NotImplementedError


def score_ecosystem_maturity_penalty(
    search_results: CompanySearchResponse,
    funding_milestones: FundingMilestoneTimeseriesResponse,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore:
    """Penalty when the space is too crowded to realistically out-build.

    Source: company_search (competitor density) + funding_milestone_timeseries.
    Scale: 0-10, 10 = low external maturity (safe to build), 0 = crowded (risky).
    """
    raise NotImplementedError
