from datetime import datetime

from data.provenance import ProvenanceRecord
from data.schemas import (
    CompanyEnrichmentResponse,
    CompanySearchResponse,
    DecisionMakersResponse,
    FundingMilestoneTimeseriesResponse,
    HeadcountTimeseriesResponse,
    WebTrafficResponse,
)
from scoring.schemas import Criterion, CriterionScore


def _make_evidence(
    criterion_id: str,
    raw_value: float,
    source_field: str,
    api_call_id: str,
) -> ProvenanceRecord:
    return ProvenanceRecord(
        criterion_id=criterion_id,
        raw_value=raw_value,
        source_field=source_field,
        api_call_id=api_call_id,
        timestamp=datetime.utcnow(),
    )


def score_capability_match(
    search_results: CompanySearchResponse | None,
    enrichment: CompanyEnrichmentResponse | None,
    taxonomy_tags: list[str],
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore | None:
    """How closely candidate companies' tech/product matches the target capability.

    Source: company_search + company_enrichment.technographics.
    Scale: 0-10.

    Heuristic: 0-10 based on product category overlap (exact match=10, related=6, unrelated=0).
    """
    if enrichment is None:
        return None

    company_categories = set(
        c.lower() for c in (enrichment.company.technographics.categories or [])
    )
    company_techs = set(
        t.lower() for t in (enrichment.company.technographics.technologies or [])
    )
    taxonomy_set = set(tag.lower() for tag in taxonomy_tags)

    if not taxonomy_set:
        return None

    # Check for exact category matches
    exact_matches = taxonomy_set & company_categories
    # Check for partial/related matches (substring match)
    related_matches = set()
    for tag in taxonomy_set - exact_matches:
        for cat in company_categories:
            if tag in cat or cat in tag:
                related_matches.add(tag)
                break
        else:
            for tech in company_techs:
                if tag in tech or tech in tag:
                    related_matches.add(tag)
                    break

    # Score: exact matches = 10, related = 6, no match = 0
    total_tags = len(taxonomy_set)
    if total_tags == 0:
        return None

    weighted_matches = (len(exact_matches) * 10) + (len(related_matches) * 6)
    score = min(10.0, weighted_matches / total_tags)

    return CriterionScore(
        criterion_id=criterion.id,
        score=round(score, 2),
        weight=criterion.weight,
        evidence=_make_evidence(
            criterion_id=criterion.id,
            raw_value=float(len(exact_matches) + len(related_matches)),
            source_field="company_enrichment.technographics.categories+technologies",
            api_call_id=api_call_id,
        ),
        notes=f"{len(exact_matches)} exact, {len(related_matches)} related matches",
    )


def score_complementary_customer_base(
    candidate_enrichment: CompanyEnrichmentResponse | None,
    requesting_enrichment: CompanyEnrichmentResponse | None,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore | None:
    """Degree of non-overlapping customer/market fit.

    Source: company_enrichment (industry, customer segment signals).
    Scale: 0-10, 10 = highly complementary, 0 = direct competitor overlap.

    Heuristic: 1 - (overlap in industry/segment), 0-10.
    """
    if candidate_enrichment is None or requesting_enrichment is None:
        return None

    candidate_industry = (candidate_enrichment.company.industry or "").lower()
    requesting_industry = (requesting_enrichment.company.industry or "").lower()

    if not candidate_industry or not requesting_industry:
        return None

    # Same industry = low complementarity (potential competitor)
    if candidate_industry == requesting_industry:
        score = 2.0
    # Related industries (substring match) = moderate complementarity
    elif candidate_industry in requesting_industry or requesting_industry in candidate_industry:
        score = 5.0
    # Different industries = high complementarity
    else:
        score = 8.0

    # Check for overlapping categories as additional signal
    candidate_cats = set(
        c.lower() for c in (candidate_enrichment.company.technographics.categories or [])
    )
    requesting_cats = set(
        c.lower() for c in (requesting_enrichment.company.technographics.categories or [])
    )
    if candidate_cats and requesting_cats:
        overlap = len(candidate_cats & requesting_cats)
        total = len(candidate_cats | requesting_cats)
        if total > 0:
            overlap_ratio = overlap / total
            # Reduce score if high category overlap (more competitive)
            score = score * (1 - 0.5 * overlap_ratio)

    return CriterionScore(
        criterion_id=criterion.id,
        score=round(max(0.0, min(10.0, score)), 2),
        weight=criterion.weight,
        evidence=_make_evidence(
            criterion_id=criterion.id,
            raw_value=score,
            source_field="company_enrichment.industry+categories",
            api_call_id=api_call_id,
        ),
        notes=f"Candidate: {candidate_industry}, Requesting: {requesting_industry}",
    )


def score_decision_maker_reachability(
    decision_makers: DecisionMakersResponse | None,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore | None:
    """Presence of named, reachable decision-makers at candidate companies.

    Source: decision_makers_filter / person_screener.
    Scale: 0-10, 10 = multiple senior, reachable contacts identified.

    Heuristic: count of decision_makers in people.decision_makers array, capped at 10.
    """
    if decision_makers is None:
        return None

    dm_count = len(decision_makers.decision_makers) if decision_makers.decision_makers else 0
    if dm_count == 0:
        return None

    # 5+ decision makers = excellent reachability (10/10)
    score = min(10.0, (dm_count / 5.0) * 10.0)

    return CriterionScore(
        criterion_id=criterion.id,
        score=round(score, 2),
        weight=criterion.weight,
        evidence=_make_evidence(
            criterion_id=criterion.id,
            raw_value=float(dm_count),
            source_field="decision_makers_filter.decision_makers.count",
            api_call_id=api_call_id,
        ),
        notes=f"{dm_count} decision makers identified",
    )


def score_partnership_stability_signal(
    funding_milestones: FundingMilestoneTimeseriesResponse | None,
    headcount: HeadcountTimeseriesResponse | None,
    web_traffic: WebTrafficResponse | None,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore | None:
    """Signals the company is a stable, ongoing entity, not distressed.

    Source: funding_milestone_timeseries + headcount_timeseries + web_traffic.
    Scale: 0-10.
    """
    signals = []

    # Check headcount trend
    if headcount and headcount.series and len(headcount.series) >= 2:
        recent = headcount.series[-1].headcount
        older = headcount.series[0].headcount
        if older > 0:
            growth = (recent - older) / older
            if growth > 0.1:
                signals.append(8.0)  # Growing
            elif growth > -0.05:
                signals.append(6.0)  # Stable
            else:
                signals.append(2.0)  # Shrinking
        else:
            signals.append(5.0)
    elif headcount and headcount.series:
        signals.append(5.0)  # Single data point, neutral

    # Check funding recency
    if funding_milestones and funding_milestones.milestones:
        recent_funding = len([m for m in funding_milestones.milestones])
        if recent_funding >= 2:
            signals.append(7.0)  # Multiple rounds = established
        else:
            signals.append(5.0)
    else:
        signals.append(3.0)  # No funding data = slightly risky

    # Check web traffic stability
    if web_traffic and web_traffic.series and len(web_traffic.series) >= 2:
        recent_visits = web_traffic.series[-1].monthly_visits
        older_visits = web_traffic.series[0].monthly_visits
        if older_visits > 0:
            visit_growth = (recent_visits - older_visits) / older_visits
            if visit_growth > 0:
                signals.append(7.0)
            elif visit_growth > -0.2:
                signals.append(5.0)
            else:
                signals.append(2.0)
        else:
            signals.append(4.0)
    elif web_traffic and web_traffic.series:
        signals.append(5.0)

    if not signals:
        return None

    score = sum(signals) / len(signals)

    return CriterionScore(
        criterion_id=criterion.id,
        score=round(score, 2),
        weight=criterion.weight,
        evidence=_make_evidence(
            criterion_id=criterion.id,
            raw_value=float(len(signals)),
            source_field="funding+headcount+web_traffic.stability",
            api_call_id=api_call_id,
        ),
        notes=f"Stability signals from {len(signals)} data sources",
    )


def score_integration_friction(
    enrichment: CompanyEnrichmentResponse | None,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore | None:
    """Estimated friction to integrate: API-first vs closed platform.

    Source: company_enrichment + LLM inference from product/docs signals.
    Scale: 0-10, 10 = low friction.

    Heuristic: based on technographics (API-friendly tech = lower friction).
    """
    if enrichment is None:
        return None

    techs = set(t.lower() for t in (enrichment.company.technographics.technologies or []))
    categories = set(c.lower() for c in (enrichment.company.technographics.categories or []))

    if not techs and not categories:
        return None

    # API-friendly technologies suggest lower integration friction
    api_friendly = {"rest", "graphql", "api", "sdk", "webhook", "json", "oauth", "grpc"}
    api_matches = techs & api_friendly

    # Platform categories suggest higher friction
    platform_categories = {"platform", "suite", "enterprise", "proprietary"}
    platform_matches = categories & platform_categories

    # Base score
    score = 5.0
    # Boost for API-friendly tech
    score += len(api_matches) * 1.5
    # Penalty for platform-heavy categories
    score -= len(platform_matches) * 1.0

    score = max(0.0, min(10.0, score))

    return CriterionScore(
        criterion_id=criterion.id,
        score=round(score, 2),
        weight=criterion.weight,
        evidence=_make_evidence(
            criterion_id=criterion.id,
            raw_value=float(len(api_matches)),
            source_field="company_enrichment.technographics",
            api_call_id=api_call_id,
        ),
        notes=f"{len(api_matches)} API-friendly techs, {len(platform_matches)} platform categories",
    )
