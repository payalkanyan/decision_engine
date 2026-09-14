"""Tests for cli/main.py — the CLI entry point.

All external dependencies (CachingClient, LLM) are mocked. The scoring
engine runs against the real rubric.yaml and mock enrichment data.
"""

from datetime import UTC, date, datetime
from unittest.mock import patch

import pytest

from cli.main import main
from data.caching_client import ApiProvenanceRecord
from data.schemas import (
    CompanyEnrichment,
    CompanyEnrichmentResponse,
    FundingSummary,
    HeadcountDataPoint,
    HeadcountTimeseriesResponse,
    JobPosting,
    JobsResponse,
    Technographics,
)
from llm.schemas import GoalClassification


@pytest.fixture
def mock_enrichment() -> CompanyEnrichmentResponse:
    return CompanyEnrichmentResponse(
        company=CompanyEnrichment(
            company_name="TechCorp Inc",
            domain="techcorp.com",
            industry="Enterprise Software",
            employee_count=500,
            technographics=Technographics(
                technologies=["Python", "PyTorch", "Kubernetes", "AWS"],
                categories=["Cloud Infrastructure", "Developer Tools", "AI"],
            ),
            funding=FundingSummary(
                total_raised=50000000,
                latest_round_type="Series B",
                latest_round_amount=30000000,
            ),
        )
    )


@pytest.fixture
def mock_provenance() -> ApiProvenanceRecord:
    return ApiProvenanceRecord(
        api_call_id="test-api-call-id",
        timestamp=datetime.now(UTC),
        cache_hit=False,
        request_fields=["name=Acme"],
    )


@pytest.fixture
def mock_jobs() -> JobsResponse:
    """Mock jobs for the requesting company (enough for strong hiring velocity)."""
    return JobsResponse(
        jobs=[
            JobPosting(
                title=f"AI/ML Engineer {i}",
                department="Engineering",
                company_name="TechCorp Inc",
                posted_date=date(2024, 1, 15),
            )
            for i in range(12)
        ],
        total_count=12,
    )


@pytest.fixture
def mock_headcount() -> HeadcountTimeseriesResponse:
    """Mock headcount timeseries for the requesting company."""
    return HeadcountTimeseriesResponse(
        company_name="TechCorp Inc",
        series=[
            HeadcountDataPoint(date=date(2024, 1, 1), headcount=500),
            HeadcountDataPoint(date=date(2024, 6, 1), headcount=550),
        ],
    )


@pytest.fixture
def mock_classification() -> GoalClassification:
    return GoalClassification(
        goal="We want to enter AI voice",
        taxonomy_tags=["ai/ml", "speech-to-text", "voice-agents"],
        search_keywords=["voice AI"],
        build_signals=["NLP team"],
        partner_signals=["voice API providers"],
        acquire_signals=["voice startups"],
    )


@pytest.fixture
def mock_candidates() -> list[CompanyEnrichmentResponse]:
    """Return 3 mock candidate companies for partner/acquire paths."""
    return [
        CompanyEnrichmentResponse(
            company=CompanyEnrichment(
                company_name=f"Candidate {i}",
                domain=f"candidate{i}.com",
                industry="AI Voice",
                employee_count=50 + i * 20,
                technographics=Technographics(
                    technologies=["Python", "AWS"],
                    categories=["AI"],
                ),
                funding=FundingSummary(
                    total_raised=10000000 * (i + 1),
                    latest_round_type="Series A",
                    latest_round_amount=5000000,
                ),
            )
        )
        for i in range(3)
    ]


class TestCLIParsing:
    def test_cli_requires_my_company(self) -> None:
        with patch("sys.argv", ["cli", "--capability", "AI voice"]), pytest.raises(SystemExit):
            main()

    def test_cli_requires_capability(self) -> None:
        with patch("sys.argv", ["cli", "--my-company", "Acme"]), pytest.raises(SystemExit):
            main()


class TestCLIPipeline:
    @patch("cli.main.synthesize_build_reasoning")
    @patch("cli.main.synthesize_partner_reasoning")
    @patch("cli.main.synthesize_acquire_reasoning")
    @patch("cli.main.get_candidates")
    @patch("cli.main.CachingClient")
    def test_cli_calls_enrichment_and_candidates(
        self,
        mock_client_cls,
        mock_get_candidates,
        mock_partner_reason,
        mock_build_reason,
        mock_acquire_reason,
        mock_enrichment: CompanyEnrichmentResponse,
        mock_provenance: ApiProvenanceRecord,
        mock_candidates: list[CompanyEnrichmentResponse],
        mock_jobs: JobsResponse,
        mock_headcount: HeadcountTimeseriesResponse,
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.return_value = (mock_enrichment, mock_provenance)
        mock_client.get_jobs.return_value = (mock_jobs, mock_provenance)
        mock_client.get_headcount_timeseries.return_value = (
            mock_headcount,
            mock_provenance,
        )
        mock_get_candidates.return_value = mock_candidates

        with patch("sys.argv", ["cli", "--my-company", "Acme", "--capability", "AI voice"]):
            main()

        mock_client.get_company_enrichment.assert_called_with("Acme")
        assert mock_get_candidates.call_count == 3  # build, partner, acquire

    @patch("cli.main.synthesize_build_reasoning")
    @patch("cli.main.synthesize_partner_reasoning")
    @patch("cli.main.synthesize_acquire_reasoning")
    @patch("cli.main.get_candidates")
    @patch("cli.main.CachingClient")
    def test_cli_prints_strategy_analysis(
        self,
        mock_client_cls,
        mock_get_candidates,
        mock_partner_reason,
        mock_build_reason,
        mock_acquire_reason,
        mock_enrichment: CompanyEnrichmentResponse,
        mock_provenance: ApiProvenanceRecord,
        mock_candidates: list[CompanyEnrichmentResponse],
        mock_jobs: JobsResponse,
        mock_headcount: HeadcountTimeseriesResponse,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.return_value = (mock_enrichment, mock_provenance)
        mock_client.get_jobs.return_value = (mock_jobs, mock_provenance)
        mock_client.get_headcount_timeseries.return_value = (
            mock_headcount,
            mock_provenance,
        )
        mock_get_candidates.return_value = mock_candidates

        with patch("sys.argv", ["cli", "--my-company", "Acme", "--capability", "AI voice"]):
            main()

        captured = capsys.readouterr()
        assert "Acme" in captured.out
        assert "AI voice" in captured.out
        assert "Build:" in captured.out
        assert "Partner:" in captured.out
        assert "Acquire:" in captured.out

    @patch("cli.main.synthesize_build_reasoning")
    @patch("cli.main.synthesize_partner_reasoning")
    @patch("cli.main.synthesize_acquire_reasoning")
    @patch("cli.main.get_candidates")
    @patch("cli.main.CachingClient")
    def test_cli_error_propagates(
        self,
        mock_client_cls,
        mock_get_candidates,
        mock_partner_reason,
        mock_build_reason,
        mock_acquire_reason,
        mock_enrichment: CompanyEnrichmentResponse,
        mock_provenance: ApiProvenanceRecord,
        mock_candidates: list[CompanyEnrichmentResponse],
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.side_effect = ValueError("Company not found: UnknownCo")
        mock_get_candidates.return_value = mock_candidates

        with (
            patch(
                "sys.argv",
                ["cli", "--my-company", "UnknownCo", "--capability", "AI voice"],
            ),
            pytest.raises(ValueError, match="Company not found"),
        ):
            main()
