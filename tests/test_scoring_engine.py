"""Tests for the scoring engine with mocked Crustdata fixtures."""

from datetime import date, datetime

from data.schemas import (
    CompanyEnrichment,
    CompanyEnrichmentResponse,
    CompanySearchResponse,
    CompanySearchResult,
    DecisionMaker,
    DecisionMakersResponse,
    FundingMilestone,
    FundingMilestoneTimeseriesResponse,
    FundingSummary,
    HeadcountDataPoint,
    HeadcountTimeseriesResponse,
    JobPosting,
    JobsResponse,
    LinkedInPost,
    LinkedInPostsResponse,
    PersonScreenerResponse,
    PersonScreenerResult,
    Technographics,
    WebTrafficDataPoint,
    WebTrafficResponse,
)
from scoring.engine import (
    Evidence,
    build_output,
    load_rubric_yaml,
    score_acquire_path,
    score_all,
    score_build_path,
    score_partner_path,
    score_path,
)
from scoring.schemas import Rubric


def _load_test_rubric() -> Rubric:
    """Load the actual rubric.yaml for testing."""
    return load_rubric_yaml("rubric.yaml")


def _make_own_enrichment() -> CompanyEnrichmentResponse:
    return CompanyEnrichmentResponse(
        company=CompanyEnrichment(
            company_name="Acme Corp",
            domain="acme.com",
            industry="Enterprise Software",
            employee_count=500,
            technographics=Technographics(
                technologies=["Python", "AWS", "React", "PostgreSQL"],
                categories=["Cloud Infrastructure", "Developer Tools"],
            ),
            funding=FundingSummary(
                total_raised=50000000,
                latest_round_type="Series B",
                latest_round_amount=30000000,
            ),
        )
    )


def _make_candidate_enrichment() -> CompanyEnrichmentResponse:
    return CompanyEnrichmentResponse(
        company=CompanyEnrichment(
            company_name="VoiceAI Inc",
            domain="voiceai.io",
            industry="Artificial Intelligence",
            employee_count=25,
            technographics=Technographics(
                technologies=["Python", "TensorFlow", "API", "WebRTC"],
                categories=["Speech-to-Text", "Voice Agents", "Real-time Audio"],
            ),
            funding=FundingSummary(
                total_raised=5000000,
                latest_round_type="Seed",
                latest_round_amount=3000000,
            ),
        )
    )


def _make_own_jobs() -> JobsResponse:
    return JobsResponse(
        jobs=[
            JobPosting(
                title="ML Engineer",
                department="Engineering",
                company_name="Acme Corp",
                posted_date=date(2024, 1, 15),
            ),
            JobPosting(
                title="Senior Backend Engineer",
                department="Engineering",
                company_name="Acme Corp",
                posted_date=date(2024, 2, 1),
            ),
            JobPosting(
                title="DevOps Engineer",
                department="Infrastructure",
                company_name="Acme Corp",
                posted_date=date(2024, 2, 15),
            ),
        ],
        total_count=3,
    )


def _make_market_jobs() -> JobsResponse:
    return JobsResponse(
        jobs=[
            JobPosting(
                title=f"Voice Engineer {i}",
                department="Engineering",
                company_name=f"Company {i}",
                posted_date=date(2024, 1, 1),
            )
            for i in range(20)
        ],
        total_count=20,
    )


def _make_market_search() -> CompanySearchResponse:
    return CompanySearchResponse(
        results=[
            CompanySearchResult(
                name=f"Competitor {i}",
                domain=f"competitor{i}.com",
                industry="Artificial Intelligence",
                employee_count=50 * i,
            )
            for i in range(5)
        ],
        total_count=5,
    )


def _make_candidate_decision_makers() -> DecisionMakersResponse:
    return DecisionMakersResponse(
        company_name="VoiceAI Inc",
        decision_makers=[
            DecisionMaker(
                name="Jane Smith",
                title="CEO",
                seniority="C-level",
                company_name="VoiceAI Inc",
            ),
            DecisionMaker(
                name="John Doe",
                title="CTO",
                seniority="C-level",
                company_name="VoiceAI Inc",
            ),
            DecisionMaker(
                name="Alice Johnson",
                title="VP of Engineering",
                seniority="VP",
                company_name="VoiceAI Inc",
            ),
        ],
    )


def _make_candidate_funding() -> FundingMilestoneTimeseriesResponse:
    return FundingMilestoneTimeseriesResponse(
        company_name="VoiceAI Inc",
        milestones=[
            FundingMilestone(
                date=date(2023, 6, 1),
                round_type="Seed",
                amount=3000000,
                investors=["Tech Ventures"],
            ),
        ],
    )


def _make_candidate_headcount() -> HeadcountTimeseriesResponse:
    return HeadcountTimeseriesResponse(
        company_name="VoiceAI Inc",
        series=[
            HeadcountDataPoint(date=date(2023, 1, 1), headcount=10),
            HeadcountDataPoint(date=date(2023, 6, 1), headcount=15),
            HeadcountDataPoint(date=date(2024, 1, 1), headcount=25),
        ],
    )


def _make_candidate_web_traffic() -> WebTrafficResponse:
    return WebTrafficResponse(
        domain="voiceai.io",
        series=[
            WebTrafficDataPoint(date=date(2023, 6, 1), monthly_visits=5000),
            WebTrafficDataPoint(date=date(2024, 1, 1), monthly_visits=12000),
        ],
    )


def _make_acquire_persons() -> PersonScreenerResponse:
    return PersonScreenerResponse(
        results=[
            PersonScreenerResult(
                name="Jane Smith",
                title="CEO",
                company_name="VoiceAI Inc",
                seniority="C-level",
            ),
            PersonScreenerResult(
                name="John Doe",
                title="CTO",
                company_name="VoiceAI Inc",
                seniority="C-level",
            ),
            PersonScreenerResult(
                name="Alice Johnson",
                title="VP Engineering",
                company_name="VoiceAI Inc",
                seniority="VP",
            ),
        ],
        total_count=3,
    )


def _make_acquire_linkedin() -> LinkedInPostsResponse:
    return LinkedInPostsResponse(
        company_name="VoiceAI Inc",
        posts=[
            LinkedInPost(
                author_name="Jane Smith",
                author_title="CEO",
                content="Excited about our latest voice AI breakthrough!",
                posted_date=datetime(2024, 1, 15),
                engagement=150,
            ),
            LinkedInPost(
                author_name="John Doe",
                author_title="CTO",
                content="Hiring voice engineers!",
                posted_date=datetime(2024, 2, 1),
                engagement=75,
            ),
        ],
    )


def _make_full_evidence() -> Evidence:
    return Evidence(
        taxonomy_tags=["speech-to-text", "voice-agents", "real-time-audio"],
        own_jobs=_make_own_jobs(),
        own_enrichment=_make_own_enrichment(),
        market_jobs=_make_market_jobs(),
        market_search=_make_market_search(),
        candidate_enrichment=_make_candidate_enrichment(),
        candidate_decision_makers=_make_candidate_decision_makers(),
        candidate_funding=_make_candidate_funding(),
        candidate_headcount=_make_candidate_headcount(),
        candidate_web_traffic=_make_candidate_web_traffic(),
        acquire_enrichment=_make_candidate_enrichment(),
        acquire_headcount=_make_candidate_headcount(),
        acquire_funding=_make_candidate_funding(),
        acquire_persons=_make_acquire_persons(),
        acquire_linkedin=_make_acquire_linkedin(),
        acquire_decision_makers=_make_candidate_decision_makers(),
        api_call_ids={
            "own_jobs": "api-jobs-001",
            "own_enrichment": "api-enrich-001",
            "market_jobs": "api-jobs-002",
            "market_search": "api-search-001",
            "candidate_enrichment": "api-enrich-002",
            "candidate_decision_makers": "api-dm-001",
            "candidate_funding": "api-fund-001",
            "candidate_headcount": "api-hc-001",
            "candidate_web_traffic": "api-traf-001",
            "acquire_enrichment": "api-enrich-003",
            "acquire_headcount": "api-hc-002",
            "acquire_funding": "api-fund-002",
            "acquire_persons": "api-pers-001",
            "acquire_linkedin": "api-li-001",
            "acquire_decision_makers": "api-dm-002",
        },
    )


class TestLoadRubric:
    def test_loads_rubric_yaml(self):
        rubric = _load_test_rubric()
        assert rubric.version == 1.0
        assert "build" in rubric.paths
        assert "partner" in rubric.paths
        assert "acquire" in rubric.paths

    def test_build_path_has_criteria(self):
        rubric = _load_test_rubric()
        build = rubric.paths["build"]
        assert len(build.criteria) == 5
        assert build.criteria[0].id == "internal_hiring_velocity"

    def test_partner_path_has_criteria(self):
        rubric = _load_test_rubric()
        partner = rubric.paths["partner"]
        assert len(partner.criteria) == 5
        assert partner.criteria[0].id == "capability_match"

    def test_acquire_path_has_criteria(self):
        rubric = _load_test_rubric()
        acquire = rubric.paths["acquire"]
        assert len(acquire.criteria) == 5
        assert acquire.criteria[0].id == "capability_match"


class TestScoreBuildPath:
    def test_scores_build_path_with_full_data(self):
        rubric = _load_test_rubric()
        evidence = _make_full_evidence()

        result = score_build_path(evidence, rubric)

        assert result.path == "build"
        assert 0 <= result.score <= 10
        assert len(result.criteria) == 5

    def test_build_path_has_evidence_trail(self):
        rubric = _load_test_rubric()
        evidence = _make_full_evidence()

        result = score_build_path(evidence, rubric)

        for cs in result.criteria:
            if not cs.excluded:
                assert cs.evidence is not None
                assert cs.evidence.criterion_id == cs.criterion_id
                assert cs.evidence.api_call_id != ""

    def test_build_path_handles_missing_data(self):
        rubric = _load_test_rubric()
        evidence = Evidence(
            taxonomy_tags=["speech-to-text"],
            own_jobs=None,
            own_enrichment=None,
        )

        result = score_build_path(evidence, rubric)

        # Should still return a score (may be 0 if all excluded)
        assert result.path == "build"
        assert result.score >= 0

    def test_weights_renormalize_when_missing(self):
        rubric = _load_test_rubric()
        evidence = Evidence(
            taxonomy_tags=["speech-to-text"],
            own_jobs=_make_own_jobs(),
            own_enrichment=None,  # Missing
        )

        result = score_build_path(evidence, rubric)

        included = [cs for cs in result.criteria if not cs.excluded]
        if included:
            total_weight = sum(cs.weight for cs in included)
            assert abs(total_weight - 1.0) < 0.01


class TestScorePartnerPath:
    def test_scores_partner_path_with_full_data(self):
        rubric = _load_test_rubric()
        evidence = _make_full_evidence()

        result = score_partner_path(evidence, rubric)

        assert result.path == "partner"
        assert 0 <= result.score <= 10
        assert len(result.criteria) == 5

    def test_partner_path_has_evidence_trail(self):
        rubric = _load_test_rubric()
        evidence = _make_full_evidence()

        result = score_partner_path(evidence, rubric)

        for cs in result.criteria:
            if not cs.excluded:
                assert cs.evidence is not None
                assert cs.evidence.criterion_id == cs.criterion_id

    def test_partner_path_handles_missing_data(self):
        rubric = _load_test_rubric()
        evidence = Evidence(taxonomy_tags=["speech-to-text"])

        result = score_partner_path(evidence, rubric)

        assert result.path == "partner"
        assert result.score >= 0


class TestScoreAcquirePath:
    def test_scores_acquire_path_with_full_data(self):
        rubric = _load_test_rubric()
        evidence = _make_full_evidence()

        result = score_acquire_path(evidence, rubric)

        assert result.path == "acquire"
        assert 0 <= result.score <= 10
        assert len(result.criteria) == 5

    def test_acquire_path_has_evidence_trail(self):
        rubric = _load_test_rubric()
        evidence = _make_full_evidence()

        result = score_acquire_path(evidence, rubric)

        for cs in result.criteria:
            if not cs.excluded:
                assert cs.evidence is not None
                assert cs.evidence.criterion_id == cs.criterion_id

    def test_acquire_path_handles_missing_data(self):
        rubric = _load_test_rubric()
        evidence = Evidence(taxonomy_tags=["speech-to-text"])

        result = score_acquire_path(evidence, rubric)

        assert result.path == "acquire"
        assert result.score >= 0


class TestScoreAll:
    def test_scores_all_paths(self):
        rubric = _load_test_rubric()
        evidence = _make_full_evidence()

        results = score_all(rubric, evidence)

        assert len(results) == 3
        paths = [r.path for r in results]
        assert "build" in paths
        assert "partner" in paths
        assert "acquire" in paths

    def test_all_paths_have_scores(self):
        rubric = _load_test_rubric()
        evidence = _make_full_evidence()

        results = score_all(rubric, evidence)

        for r in results:
            assert 0 <= r.score <= 10


class TestScorePath:
    def test_score_single_path(self):
        rubric = _load_test_rubric()
        evidence = _make_full_evidence()

        result = score_path("build", rubric, evidence)
        assert result.path == "build"

    def test_score_invalid_path_raises(self):
        rubric = _load_test_rubric()
        evidence = _make_full_evidence()

        import pytest

        with pytest.raises(ValueError, match="Unknown path"):
            score_path("invalid", rubric, evidence)


class TestBuildOutput:
    def test_build_output_assembles_correctly(self):
        rubric = _load_test_rubric()
        evidence = _make_full_evidence()

        path_scores = score_all(rubric, evidence)
        output = build_output(path_scores, rubric)

        assert "build" in output.final_scores
        assert "partner" in output.final_scores
        assert "acquire" in output.final_scores
        assert output.recommendation.primary_path in ["build", "partner", "acquire"]
        assert len(output.evidence_trail) > 0

    def test_close_call_detection(self):
        rubric = _load_test_rubric()

        from scoring.schemas import CriterionScore, PathScore

        path_scores = [
            PathScore(
                path="build",
                score=7.5,
                weight_in_final_decision=0.34,
                criteria=[
                    CriterionScore(
                        criterion_id="test",
                        score=7.5,
                        weight=1.0,
                        evidence=None,
                    )
                ],
            ),
            PathScore(
                path="partner",
                score=7.0,
                weight_in_final_decision=0.33,
                criteria=[
                    CriterionScore(
                        criterion_id="test",
                        score=7.0,
                        weight=1.0,
                        evidence=None,
                    )
                ],
            ),
            PathScore(
                path="acquire",
                score=3.0,
                weight_in_final_decision=0.33,
                criteria=[
                    CriterionScore(
                        criterion_id="test",
                        score=3.0,
                        weight=1.0,
                        evidence=None,
                    )
                ],
            ),
        ]

        output = build_output(path_scores, rubric)

        assert output.recommendation.is_close_call is True
        assert output.recommendation.close_call_alternative == "partner"

    def test_not_close_call_when_gap_large(self):
        rubric = _load_test_rubric()

        from scoring.schemas import CriterionScore, PathScore

        path_scores = [
            PathScore(
                path="build",
                score=8.0,
                weight_in_final_decision=0.34,
                criteria=[
                    CriterionScore(
                        criterion_id="test",
                        score=8.0,
                        weight=1.0,
                        evidence=None,
                    )
                ],
            ),
            PathScore(
                path="partner",
                score=5.0,
                weight_in_final_decision=0.33,
                criteria=[
                    CriterionScore(
                        criterion_id="test",
                        score=5.0,
                        weight=1.0,
                        evidence=None,
                    )
                ],
            ),
            PathScore(
                path="acquire",
                score=3.0,
                weight_in_final_decision=0.33,
                criteria=[
                    CriterionScore(
                        criterion_id="test",
                        score=3.0,
                        weight=1.0,
                        evidence=None,
                    )
                ],
            ),
        ]

        output = build_output(path_scores, rubric)

        assert output.recommendation.is_close_call is False
        assert output.recommendation.close_call_alternative is None

    def test_generated_at_timestamp(self):
        rubric = _load_test_rubric()
        evidence = _make_full_evidence()

        path_scores = score_all(rubric, evidence)
        output = build_output(path_scores, rubric)

        assert output.generated_at is not None
