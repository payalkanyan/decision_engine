from datetime import datetime

from data.provenance import ProvenanceRecord
from data.schemas import (
    CompanyEnrichmentResponse,
    CompanySearchResponse,
    FundingMilestoneTimeseriesResponse,
    HeadcountTimeseriesResponse,
    JobsResponse,
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


def score_internal_hiring_velocity(
    jobs: JobsResponse | None,
    headcount: HeadcountTimeseriesResponse | None,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore | None:
    """Rate at which the company is already hiring for adjacent roles.

    Source: jobs_api + headcount_timeseries (own company).
    Scale: 0-10, 10 = strong existing hiring motion.

    Heuristic: len(jobs) / 12 months, normalized 0-10.
    """
    if jobs is None or not jobs.jobs:
        return None

    job_count = len(jobs.jobs)
    # Normalize: 12+ jobs in 12 months = strong motion (10/10)
    raw_velocity = job_count / 12.0
    score = min(10.0, raw_velocity * 10.0)

    return CriterionScore(
        criterion_id=criterion.id,
        score=round(score, 2),
        weight=criterion.weight,
        evidence=_make_evidence(
            criterion_id=criterion.id,
            raw_value=float(job_count),
            source_field="jobs_api.jobs.count",
            api_call_id=api_call_id,
        ),
        notes=f"{job_count} jobs in 12 months, velocity={raw_velocity:.2f}",
    )


def score_existing_tech_stack_overlap(
    enrichment: CompanyEnrichmentResponse | None,
    taxonomy_tags: list[str],
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore | None:
    """Overlap between company's current tech stack and capability requirements.

    Source: company_enrichment.technographics (own company).
    Scale: 0-10, 10 = capability is a natural extension of current stack.

    Heuristic: count matching categories in market_intels vs requesting_company.
    """
    if enrichment is None:
        return None

    company_categories = set(enrichment.company.technographics.categories or [])
    if not company_categories:
        return None

    taxonomy_set = set(tag.lower() for tag in taxonomy_tags)
    categories_lower = set(c.lower() for c in company_categories)

    # Count exact or partial matches
    matches = 0
    for tag in taxonomy_set:
        for cat in categories_lower:
            if tag in cat or cat in tag:
                matches += 1
                break

    # Scale: each matching category adds points, max 10
    score = 0.0 if not taxonomy_set else min(10.0, (matches / max(len(taxonomy_set), 1)) * 10.0)

    return CriterionScore(
        criterion_id=criterion.id,
        score=round(score, 2),
        weight=criterion.weight,
        evidence=_make_evidence(
            criterion_id=criterion.id,
            raw_value=float(matches),
            source_field="company_enrichment.technographics.categories",
            api_call_id=api_call_id,
        ),
        notes=f"{matches} matching categories out of {len(taxonomy_set)} taxonomy tags",
    )


def score_talent_market_availability(
    market_jobs: JobsResponse | None,
    persons: PersonScreenerResponse | None,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore | None:
    """Depth of hireable talent pool for this capability in relevant markets.

    Source: jobs_api (market-wide) + person_screener.
    Scale: 0-10, 10 = deep, liquid talent market.

    Heuristic: count other companies with matching job postings, normalized 0-10.
    """
    if market_jobs is None:
        return None

    job_count = len(market_jobs.jobs) if market_jobs.jobs else 0
    person_count = len(persons.results) if persons and persons.results else 0

    # Combine signals: jobs across market + reachable persons
    # 50+ market jobs = deep market (10/10)
    market_score = min(10.0, (job_count / 50.0) * 10.0)
    person_score = min(10.0, (person_count / 10.0) * 10.0)

    # Weight market jobs more (70%) than person matches (30%)
    if job_count > 0 and person_count > 0:
        score = 0.7 * market_score + 0.3 * person_score
    elif job_count > 0:
        score = market_score
    else:
        return None

    return CriterionScore(
        criterion_id=criterion.id,
        score=round(score, 2),
        weight=criterion.weight,
        evidence=_make_evidence(
            criterion_id=criterion.id,
            raw_value=float(job_count),
            source_field="jobs_api.market_wide.count",
            api_call_id=api_call_id,
        ),
        notes=f"{job_count} market jobs, {person_count} reachable persons",
    )


def score_estimated_time_to_capability(
    hiring_velocity_score: CriterionScore | None,
    talent_availability_score: CriterionScore | None,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore | None:
    """Estimated months to reach competitive capability internally.

    Source: derived from internal_hiring_velocity + talent_market_availability.
    Scale: 0-10, 10 = fast (<6 months), 0 = slow (>24 months).

    Heuristic: (12 - internal_hiring_velocity) months, scaled to 0-10.
    """
    # Need at least one of the inputs
    if hiring_velocity_score is None and talent_availability_score is None:
        return None

    # Use available scores, default excluded ones to neutral
    hv = hiring_velocity_score.score if hiring_velocity_score else 5.0
    ta = talent_availability_score.score if talent_availability_score else 5.0

    # Estimated months: inverse of hiring velocity, adjusted by talent availability
    # High hiring velocity + high talent availability = fewer months
    avg_signal = (hv + ta) / 2.0
    # 10 signal → ~3 months, 0 signal → ~30 months
    estimated_months = 30 - (avg_signal * 2.7)

    # Scale to 0-10: <6 months = 10, >24 months = 0
    if estimated_months <= 6:
        score = 10.0
    elif estimated_months >= 24:
        score = 0.0
    else:
        # Linear interpolation between 6 months (10) and 24 months (0)
        score = 10.0 * (24 - estimated_months) / (24 - 6)

    # Derive provenance from the inputs (only include non-excluded criteria with evidence)
    source_ids = []
    if hiring_velocity_score and hiring_velocity_score.evidence is not None:
        source_ids.append(hiring_velocity_score.evidence.api_call_id)
    if talent_availability_score and talent_availability_score.evidence is not None:
        source_ids.append(talent_availability_score.evidence.api_call_id)

    return CriterionScore(
        criterion_id=criterion.id,
        score=round(score, 2),
        weight=criterion.weight,
        evidence=ProvenanceRecord(
            criterion_id=criterion.id,
            raw_value=round(estimated_months, 1),
            source_field="derived: internal_hiring_velocity + talent_market_availability",
            api_call_id="derived:" + ",".join(source_ids) if source_ids else "derived:none",
            timestamp=datetime.utcnow(),
        ),
        notes=f"Estimated {estimated_months:.1f} months to capability",
    )


def score_ecosystem_maturity_penalty(
    search_results: CompanySearchResponse | None,
    funding_milestones: FundingMilestoneTimeseriesResponse | None,
    criterion: Criterion,
    api_call_id: str,
) -> CriterionScore | None:
    """Penalty when the space is too crowded to realistically out-build.

    Source: company_search (competitor density) + funding_milestone_timeseries.
    Scale: 0-10, 10 = low external maturity (safe to build), 0 = crowded (risky).

    Heuristic: count competitor companies with same capability, inverse scaled 0-10.
    """
    if search_results is None:
        return None

    competitor_count = (
        search_results.total_count
        if search_results.total_count
        else len(search_results.results)
    )

    # Also factor in funding activity as maturity signal
    funding_events = len(funding_milestones.milestones) if funding_milestones else 0

    # High competitor count + high funding = crowded/ripe space
    # 0 competitors = 10 (safe to build), 20+ competitors = 0 (too crowded)
    competitor_score = max(0.0, 10.0 - (competitor_count / 20.0) * 10.0)

    # More funding events = more mature ecosystem
    funding_maturity = min(1.0, funding_events / 5.0)

    # Combine: weight competitor density (70%) and funding maturity (30%)
    score = competitor_score * (1 - 0.3 * funding_maturity)

    return CriterionScore(
        criterion_id=criterion.id,
        score=round(score, 2),
        weight=criterion.weight,
        evidence=_make_evidence(
            criterion_id=criterion.id,
            raw_value=float(competitor_count),
            source_field="company_search.competitor_count",
            api_call_id=api_call_id,
        ),
        notes=f"{competitor_count} competitors, {funding_events} funding events",
    )
