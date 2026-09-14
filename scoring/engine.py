from datetime import datetime

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
from scoring.criteria import acquire as acquire_criteria
from scoring.criteria import build as build_criteria
from scoring.criteria import partner as partner_criteria
from scoring.rubric_loader import load_rubric
from scoring.schemas import (
    AnalysisOutput,
    CandidateCompany,
    CriterionScore,
    PathScore,
    Recommendation,
    Rubric,
)


class Evidence:
    """Container for all Crustdata-enriched data used in scoring."""

    def __init__(
        self,
        taxonomy_tags: list[str],
        # Build path data
        own_jobs: JobsResponse | None = None,
        own_headcount: HeadcountTimeseriesResponse | None = None,
        own_enrichment: CompanyEnrichmentResponse | None = None,
        market_jobs: JobsResponse | None = None,
        market_search: CompanySearchResponse | None = None,
        market_funding: FundingMilestoneTimeseriesResponse | None = None,
        market_persons: PersonScreenerResponse | None = None,
        # Partner path data
        candidate_search: CompanySearchResponse | None = None,
        candidate_enrichment: CompanyEnrichmentResponse | None = None,
        candidate_decision_makers: DecisionMakersResponse | None = None,
        candidate_funding: FundingMilestoneTimeseriesResponse | None = None,
        candidate_headcount: HeadcountTimeseriesResponse | None = None,
        candidate_web_traffic: WebTrafficResponse | None = None,
        # Acquire path data
        acquire_enrichment: CompanyEnrichmentResponse | None = None,
        acquire_headcount: HeadcountTimeseriesResponse | None = None,
        acquire_funding: FundingMilestoneTimeseriesResponse | None = None,
        acquire_investors: InvestorPortfolioResponse | None = None,
        acquire_persons: PersonScreenerResponse | None = None,
        acquire_linkedin: LinkedInPostsResponse | None = None,
        acquire_decision_makers: DecisionMakersResponse | None = None,
        # API call IDs for provenance
        api_call_ids: dict[str, str] | None = None,
    ):
        self.taxonomy_tags = taxonomy_tags
        self.own_jobs = own_jobs
        self.own_headcount = own_headcount
        self.own_enrichment = own_enrichment
        self.market_jobs = market_jobs
        self.market_search = market_search
        self.market_funding = market_funding
        self.market_persons = market_persons
        self.candidate_search = candidate_search
        self.candidate_enrichment = candidate_enrichment
        self.candidate_decision_makers = candidate_decision_makers
        self.candidate_funding = candidate_funding
        self.candidate_headcount = candidate_headcount
        self.candidate_web_traffic = candidate_web_traffic
        self.acquire_enrichment = acquire_enrichment
        self.acquire_headcount = acquire_headcount
        self.acquire_funding = acquire_funding
        self.acquire_investors = acquire_investors
        self.acquire_persons = acquire_persons
        self.acquire_linkedin = acquire_linkedin
        self.acquire_decision_makers = acquire_decision_makers
        self.api_call_ids = api_call_ids or {}

    def _api_id(self, key: str) -> str:
        return self.api_call_ids.get(key, f"unknown:{key}")


def _renormalize_weights(criteria_scores: list[CriterionScore]) -> list[CriterionScore]:
    """Renormalize weights for included criteria.

    When criteria are excluded (missing data), their weights are
    redistributed proportionally to the remaining criteria.
    """
    included = [cs for cs in criteria_scores if not cs.excluded]
    if not included:
        return criteria_scores

    total_original_weight = sum(cs.weight for cs in included)
    if total_original_weight == 0:
        return criteria_scores

    # Renormalize: new_weight = old_weight / total_original_weight
    # This ensures included weights sum to 1.0
    for cs in included:
        cs.weight = round(cs.weight / total_original_weight, 4)

    return criteria_scores


def score_build_path(
    evidence: Evidence,
    rubric: Rubric,
) -> PathScore:
    """Score the build path using the provided evidence and rubric."""
    path = rubric.paths["build"]
    criteria_scores: list[CriterionScore] = []
    gaps: list[str] = []

    for criterion in path.criteria:
        result: CriterionScore | None = None

        if criterion.id == "internal_hiring_velocity":
            result = build_criteria.score_internal_hiring_velocity(
                jobs=evidence.own_jobs,
                headcount=evidence.own_headcount,
                criterion=criterion,
                api_call_id=evidence._api_id("own_jobs"),
            )
        elif criterion.id == "existing_tech_stack_overlap":
            result = build_criteria.score_existing_tech_stack_overlap(
                enrichment=evidence.own_enrichment,
                taxonomy_tags=evidence.taxonomy_tags,
                criterion=criterion,
                api_call_id=evidence._api_id("own_enrichment"),
            )
        elif criterion.id == "talent_market_availability":
            result = build_criteria.score_talent_market_availability(
                market_jobs=evidence.market_jobs,
                persons=evidence.market_persons,
                criterion=criterion,
                api_call_id=evidence._api_id("market_jobs"),
            )
        elif criterion.id == "estimated_time_to_capability":
            # This is derived from other criteria
            hv_score = next(
                (cs for cs in criteria_scores if cs.criterion_id == "internal_hiring_velocity"),
                None,
            )
            ta_score = next(
                (cs for cs in criteria_scores if cs.criterion_id == "talent_market_availability"),
                None,
            )
            result = build_criteria.score_estimated_time_to_capability(
                hiring_velocity_score=hv_score,
                talent_availability_score=ta_score,
                criterion=criterion,
                api_call_id=evidence._api_id("own_jobs"),
            )
        elif criterion.id == "ecosystem_maturity_penalty":
            result = build_criteria.score_ecosystem_maturity_penalty(
                search_results=evidence.market_search,
                funding_milestones=evidence.market_funding,
                criterion=criterion,
                api_call_id=evidence._api_id("market_search"),
            )

        if result is not None:
            criteria_scores.append(result)
        else:
            # Mark as excluded due to missing data
            excluded_score = CriterionScore(
                criterion_id=criterion.id,
                score=0.0,
                weight=criterion.weight,
                evidence=None,
                excluded=True,
                notes="Excluded: missing data",
            )
            criteria_scores.append(excluded_score)
            gaps.append(f"Build criterion '{criterion.id}': missing data")

    # Renormalize weights
    criteria_scores = _renormalize_weights(criteria_scores)

    # Calculate weighted sum
    included = [cs for cs in criteria_scores if not cs.excluded]
    final_score = sum(cs.score * cs.weight for cs in included) if included else 0.0

    return PathScore(
        path="build",
        score=round(final_score, 2),
        weight_in_final_decision=path.weight_in_final_decision,
        criteria=criteria_scores,
    )


def score_partner_path(
    evidence: Evidence,
    rubric: Rubric,
) -> PathScore:
    """Score the partner path using the provided evidence and rubric."""
    path = rubric.paths["partner"]
    criteria_scores: list[CriterionScore] = []
    gaps: list[str] = []

    for criterion in path.criteria:
        result: CriterionScore | None = None

        if criterion.id == "capability_match":
            result = partner_criteria.score_capability_match(
                search_results=evidence.candidate_search,
                enrichment=evidence.candidate_enrichment,
                taxonomy_tags=evidence.taxonomy_tags,
                criterion=criterion,
                api_call_id=evidence._api_id("candidate_enrichment"),
            )
        elif criterion.id == "complementary_customer_base":
            result = partner_criteria.score_complementary_customer_base(
                candidate_enrichment=evidence.candidate_enrichment,
                requesting_enrichment=evidence.own_enrichment,
                criterion=criterion,
                api_call_id=evidence._api_id("candidate_enrichment"),
            )
        elif criterion.id == "decision_maker_reachability":
            result = partner_criteria.score_decision_maker_reachability(
                decision_makers=evidence.candidate_decision_makers,
                criterion=criterion,
                api_call_id=evidence._api_id("candidate_decision_makers"),
            )
        elif criterion.id == "partnership_stability_signal":
            result = partner_criteria.score_partnership_stability_signal(
                funding_milestones=evidence.candidate_funding,
                headcount=evidence.candidate_headcount,
                web_traffic=evidence.candidate_web_traffic,
                criterion=criterion,
                api_call_id=evidence._api_id("candidate_funding"),
            )
        elif criterion.id == "integration_friction":
            result = partner_criteria.score_integration_friction(
                enrichment=evidence.candidate_enrichment,
                criterion=criterion,
                api_call_id=evidence._api_id("candidate_enrichment"),
            )

        if result is not None:
            criteria_scores.append(result)
        else:
            excluded_score = CriterionScore(
                criterion_id=criterion.id,
                score=0.0,
                weight=criterion.weight,
                evidence=None,
                excluded=True,
                notes="Excluded: missing data",
            )
            criteria_scores.append(excluded_score)
            gaps.append(f"Partner criterion '{criterion.id}': missing data")

    criteria_scores = _renormalize_weights(criteria_scores)
    included = [cs for cs in criteria_scores if not cs.excluded]
    final_score = sum(cs.score * cs.weight for cs in included) if included else 0.0

    return PathScore(
        path="partner",
        score=round(final_score, 2),
        weight_in_final_decision=path.weight_in_final_decision,
        criteria=criteria_scores,
    )


def score_acquire_path(
    evidence: Evidence,
    rubric: Rubric,
) -> PathScore:
    """Score the acquire path using the provided evidence and rubric."""
    path = rubric.paths["acquire"]
    criteria_scores: list[CriterionScore] = []
    gaps: list[str] = []

    for criterion in path.criteria:
        result: CriterionScore | None = None

        if criterion.id == "capability_match":
            result = acquire_criteria.score_capability_match(
                search_results=evidence.candidate_search,
                enrichment=evidence.acquire_enrichment,
                taxonomy_tags=evidence.taxonomy_tags,
                criterion=criterion,
                api_call_id=evidence._api_id("acquire_enrichment"),
            )
        elif criterion.id == "acquirable_size":
            result = acquire_criteria.score_acquirable_size(
                headcount=evidence.acquire_headcount,
                criterion=criterion,
                api_call_id=evidence._api_id("acquire_headcount"),
            )
        elif criterion.id == "acquirable_funding_stage":
            result = acquire_criteria.score_acquirable_funding_stage(
                funding_milestones=evidence.acquire_funding,
                investor_portfolio=evidence.acquire_investors,
                criterion=criterion,
                api_call_id=evidence._api_id("acquire_funding"),
            )
        elif criterion.id == "team_quality_signal":
            result = acquire_criteria.score_team_quality_signal(
                persons=evidence.acquire_persons,
                linkedin_posts=evidence.acquire_linkedin,
                criterion=criterion,
                api_call_id=evidence._api_id("acquire_persons"),
            )
        elif criterion.id == "decision_maker_reachability":
            result = acquire_criteria.score_decision_maker_reachability(
                decision_makers=evidence.acquire_decision_makers,
                criterion=criterion,
                api_call_id=evidence._api_id("acquire_decision_makers"),
            )

        if result is not None:
            criteria_scores.append(result)
        else:
            excluded_score = CriterionScore(
                criterion_id=criterion.id,
                score=0.0,
                weight=criterion.weight,
                evidence=None,
                excluded=True,
                notes="Excluded: missing data",
            )
            criteria_scores.append(excluded_score)
            gaps.append(f"Acquire criterion '{criterion.id}': missing data")

    criteria_scores = _renormalize_weights(criteria_scores)
    included = [cs for cs in criteria_scores if not cs.excluded]
    final_score = sum(cs.score * cs.weight for cs in included) if included else 0.0

    return PathScore(
        path="acquire",
        score=round(final_score, 2),
        weight_in_final_decision=path.weight_in_final_decision,
        criteria=criteria_scores,
    )


def load_rubric_yaml(path: str = "rubric.yaml") -> Rubric:
    """Load rubric.yaml into a typed Rubric model."""
    return load_rubric(path)


def score_path(
    path_name: str,
    rubric: Rubric,
    evidence: Evidence,
) -> PathScore:
    """Score a single path (build/partner/acquire) using the rubric."""
    if path_name == "build":
        return score_build_path(evidence, rubric)
    elif path_name == "partner":
        return score_partner_path(evidence, rubric)
    elif path_name == "acquire":
        return score_acquire_path(evidence, rubric)
    else:
        raise ValueError(f"Unknown path: {path_name}")


def score_all(
    rubric: Rubric,
    evidence: Evidence,
) -> list[PathScore]:
    """Score all three paths and return them in rubric order."""
    return [
        score_build_path(evidence, rubric),
        score_partner_path(evidence, rubric),
        score_acquire_path(evidence, rubric),
    ]


def build_output(
    path_scores: list[PathScore],
    rubric: Rubric,
    candidate_companies: list[CandidateCompany] | None = None,
    assumptions_and_gaps: list[str] | None = None,
) -> AnalysisOutput:
    """Assemble the final AnalysisOutput from path scores.

    Determines the recommendation: highest scoring path, or "close call"
    if the top two scores are within 1.0 of each other.
    """
    final_scores = {ps.path: ps.score for ps in path_scores}

    # Determine recommendation
    sorted_scores = sorted(path_scores, key=lambda ps: ps.score, reverse=True)
    top = sorted_scores[0]
    second = sorted_scores[1] if len(sorted_scores) > 1 else None

    is_close_call = False
    close_call_alternative = None

    if second and abs(top.score - second.score) <= 1.0:
        is_close_call = True
        close_call_alternative = second.path

    # Build evidence trail from all criteria
    evidence_trail = []
    for ps in path_scores:
        for cs in ps.criteria:
            if cs.evidence is not None:
                evidence_trail.append(cs.evidence)

    # Build rationale
    if is_close_call:
        rationale = (
            f"{top.path.capitalize()} scores {top.score:.1f}, "
            f"but {close_call_alternative} is close behind at {second.score:.1f}. "
            f"Consider both paths."
        )
    else:
        rationale = (
            f"{top.path.capitalize()} is the recommended path with a score of {top.score:.1f}."
        )

    return AnalysisOutput(
        final_scores=final_scores,
        recommendation=Recommendation(
            primary_path=top.path,
            is_close_call=is_close_call,
            close_call_alternative=close_call_alternative,
            rationale=rationale,
        ),
        evidence_trail=evidence_trail,
        candidate_companies=candidate_companies or [],
        assumptions_and_gaps=assumptions_and_gaps or [],
        generated_at=datetime.utcnow(),
    )
