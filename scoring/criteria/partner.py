from data.schemas import (
    CompanyEnrichmentResponse,
    CompanySearchResponse,
    DecisionMakersResponse,
    FundingMilestoneTimeseriesResponse,
    HeadcountTimeseriesResponse,
    WebTrafficResponse,
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


def score_complementary_customer_base(
    enrichment: CompanyEnrichmentResponse,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore:
    """Degree of non-overlapping customer/market fit.

    Source: company_enrichment (industry, customer segment signals).
    Scale: 0-10, 10 = highly complementary, 0 = direct competitor overlap.
    """
    raise NotImplementedError


def score_decision_maker_reachability(
    decision_makers: DecisionMakersResponse,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore:
    """Presence of named, reachable decision-makers at candidate companies.

    Source: decision_makers_filter / person_screener.
    Scale: 0-10, 10 = multiple senior, reachable contacts identified.
    """
    raise NotImplementedError


def score_partnership_stability_signal(
    funding_milestones: FundingMilestoneTimeseriesResponse,
    headcount: HeadcountTimeseriesResponse,
    web_traffic: WebTrafficResponse,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore:
    """Signals the company is a stable, ongoing entity, not distressed.

    Source: funding_milestone_timeseries + headcount_timeseries + web_traffic.
    Scale: 0-10.
    """
    raise NotImplementedError


def score_integration_friction(
    enrichment: CompanyEnrichmentResponse,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore:
    """Estimated friction to integrate: API-first vs closed platform.

    Source: company_enrichment + LLM inference from product/docs signals.
    Scale: 0-10, 10 = low friction.
    """
    raise NotImplementedError
