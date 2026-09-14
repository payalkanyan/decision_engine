from datetime import datetime

from data.provenance import ProvenanceRecord
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


def score_acquirable_size(
    headcount: HeadcountTimeseriesResponse | None,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore | None:
    """Headcount/scale bucket suggesting the company is small enough to absorb.

    Source: headcount_timeseries.
    Scale: 0-10, 10 = ideal acquirable size (5-50 employees), 0 = too large or pre-product.
    """
    if headcount is None or not headcount.series:
        return None

    latest_hc = headcount.series[-1].headcount if headcount.series[-1].headcount else 0

    # Ideal acquirable size: 5-50 employees
    # Too small (<5) = pre-product risk, too large (>200) = too expensive
    if 5 <= latest_hc <= 50:
        score = 10.0
    elif latest_hc < 5:
        # Pre-product, scale up from 0 to 10 as hc goes 0→5
        score = max(0.0, (latest_hc / 5.0) * 6.0)
    elif latest_hc <= 100:
        # 50-100: still acquirable but larger
        score = 8.0 - ((latest_hc - 50) / 50.0) * 2.0
    elif latest_hc <= 200:
        # 100-200: getting expensive
        score = 6.0 - ((latest_hc - 100) / 100.0) * 3.0
    else:
        # 200+: likely too large
        score = max(0.0, 3.0 - ((latest_hc - 200) / 100.0) * 3.0)

    return CriterionScore(
        criterion_id=criterion.id,
        score=round(score, 2),
        weight=criterion.weight,
        evidence=_make_evidence(
            criterion_id=criterion.id,
            raw_value=float(latest_hc),
            source_field="headcount_timeseries.latest",
            api_call_id=api_call_id,
        ),
        notes=f"Latest headcount: {latest_hc}",
    )


def score_acquirable_funding_stage(
    funding_milestones: FundingMilestoneTimeseriesResponse | None,
    investor_portfolio: InvestorPortfolioResponse | None,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore | None:
    """Funding trajectory suggesting openness to acquisition.

    Source: funding_milestone_timeseries + investor_portfolio_data.
    Scale: 0-10, 10 = classic acquirable profile.
    """
    if funding_milestones is None:
        return None

    milestones = funding_milestones.milestones or []

    # No funding data = early stage, potentially acquirable
    if not milestones:
        return CriterionScore(
            criterion_id=criterion.id,
            score=6.0,
            weight=criterion.weight,
            evidence=_make_evidence(
                criterion_id=criterion.id,
                raw_value=0.0,
                source_field="funding_milestone_timeseries.milestones",
                api_call_id=api_call_id,
            ),
            notes="No funding milestones - early stage, potentially acquirable",
        )

    latest_round = milestones[-1].round_type.lower() if milestones[-1].round_type else ""

    # Earlier stages = more acquirable
    stage_scores = {
        "pre-seed": 9.0,
        "seed": 8.5,
        "angel": 8.0,
        "series a": 7.0,
        "series b": 5.0,
        "series c": 3.0,
        "series d": 2.0,
        "growth": 2.0,
        "private equity": 1.5,
    }

    score = 4.0  # Default for unknown stages
    for stage_key, stage_score in stage_scores.items():
        if stage_key in latest_round:
            score = stage_score
            break

    # Factor in number of rounds - more rounds = more investor pressure to exit
    round_count = len(milestones)
    if round_count >= 3:
        score += 1.0  # Multiple rounds increases acquisition likelihood

    # Factor in investor portfolio concentration
    if investor_portfolio and investor_portfolio.portfolio_companies:
        portfolio_size = len(investor_portfolio.portfolio_companies)
        if portfolio_size > 10:
            score += 0.5  # Active investor, more likely to push for exit

    score = min(10.0, score)

    return CriterionScore(
        criterion_id=criterion.id,
        score=round(score, 2),
        weight=criterion.weight,
        evidence=_make_evidence(
            criterion_id=criterion.id,
            raw_value=float(round_count),
            source_field="funding_milestone_timeseries.latest_round",
            api_call_id=api_call_id,
        ),
        notes=f"Latest round: {latest_round}, total rounds: {round_count}",
    )


def score_team_quality_signal(
    persons: PersonScreenerResponse | None,
    linkedin_posts: LinkedInPostsResponse | None,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore | None:
    """Signals of a strong core team worth acquiring, not just the product.

    Source: person_screener + linkedin_posts (founder/team activity).
    Scale: 0-10.
    """
    signals = []

    # Person screener signals
    if persons and persons.results:
        senior_count = 0
        for person in persons.results:
            seniority = (person.seniority or "").lower()
            if seniority in {"c-level", "vp", "director", "founder", "head"}:
                senior_count += 1

        if senior_count >= 3:
            signals.append(8.0)
        elif senior_count >= 1:
            signals.append(6.0)
        else:
            signals.append(3.0)

    # LinkedIn activity signals
    if linkedin_posts and linkedin_posts.posts:
        post_count = len(linkedin_posts.posts)
        # Active posting = engaged team
        if post_count >= 5:
            signals.append(7.0)
        elif post_count >= 2:
            signals.append(5.0)
        else:
            signals.append(3.0)

        # High engagement posts = strong thought leadership
        total_engagement = sum(p.engagement or 0 for p in linkedin_posts.posts)
        avg_engagement = total_engagement / post_count if post_count > 0 else 0
        if avg_engagement > 100:
            signals.append(9.0)
        elif avg_engagement > 20:
            signals.append(7.0)

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
            source_field="person_screener+linkedin_posts.activity",
            api_call_id=api_call_id,
        ),
        notes=f"Team quality signals from {len(signals)} data sources",
    )


def score_decision_maker_reachability(
    decision_makers: DecisionMakersResponse | None,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore | None:
    """Named founders/execs to open acquisition conversations with.

    Source: decision_makers_filter / person_screener.
    Scale: 0-10.

    Heuristic: count of decision_makers, capped at 10.
    """
    if decision_makers is None:
        return None

    dm_count = len(decision_makers.decision_makers) if decision_makers.decision_makers else 0
    if dm_count == 0:
        return None

    # 3+ decision makers = excellent reachability for acquisition talks
    score = min(10.0, (dm_count / 3.0) * 10.0)

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
        notes=f"{dm_count} decision makers for acquisition talks",
    )
