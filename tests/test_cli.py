"""Tests for cli/main.py — the CLI entry point.

All external dependencies (CachingClient, LLM) are mocked. The scoring
engine runs against the real rubric.yaml and mock enrichment data.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from cli.main import main
from data.caching_client import ApiProvenanceRecord
from data.schemas import CompanyEnrichmentResponse
from llm.schemas import GoalClassification

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


@pytest.fixture
def mock_enrichment() -> CompanyEnrichmentResponse:
    return CompanyEnrichmentResponse.model_validate(load_fixture("company_enrichment.json"))


@pytest.fixture
def mock_provenance() -> ApiProvenanceRecord:
    return ApiProvenanceRecord(
        api_call_id="test-api-call-id",
        timestamp=datetime.now(UTC),
        cache_hit=False,
        request_fields=["name=Stripe"],
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


class TestCLIParsing:
    def test_cli_requires_goal(self) -> None:
        with patch("sys.argv", ["cli", "--target-company", "Stripe"]), pytest.raises(SystemExit):
            main()

    def test_cli_requires_target_company(self) -> None:
        with patch("sys.argv", ["cli", "--goal", "AI voice"]), pytest.raises(SystemExit):
            main()


class TestCLIPipeline:
    @patch("cli.main.synthesize_narrative")
    @patch("cli.main.classify_goal")
    @patch("cli.main.CachingClient")
    def test_cli_parses_args_and_calls_enrichment(
        self,
        mock_client_cls,
        mock_classify,
        mock_synthesize,
        mock_enrichment: CompanyEnrichmentResponse,
        mock_provenance: ApiProvenanceRecord,
        mock_classification: GoalClassification,
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.return_value = (mock_enrichment, mock_provenance)
        mock_classify.return_value = mock_classification
        mock_synthesize.return_value = "Mock narrative."

        with patch(
            "sys.argv",
            ["cli", "--goal", "We want to enter AI voice", "--target-company", "Stripe"],
        ):
            main()

        mock_classify.assert_called_once_with("We want to enter AI voice")
        mock_client.get_company_enrichment.assert_called_once_with("Stripe")

    @patch("cli.main.synthesize_narrative")
    @patch("cli.main.classify_goal")
    @patch("cli.main.CachingClient")
    def test_cli_prints_recommendation_with_path_score_narrative(
        self,
        mock_client_cls,
        mock_classify,
        mock_synthesize,
        mock_enrichment,
        mock_provenance,
        mock_classification,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.return_value = (mock_enrichment, mock_provenance)
        mock_classify.return_value = mock_classification
        mock_synthesize.return_value = "Mock narrative for Stripe."

        with patch(
            "sys.argv",
            ["cli", "--goal", "We want to enter AI voice", "--target-company", "Stripe"],
        ):
            main()

        captured = capsys.readouterr()
        assert "RECOMMENDATION:" in captured.out
        assert "/10" in captured.out
        assert "Mock narrative for Stripe." in captured.out
        assert "Evidence breakdown:" in captured.out

    @patch("cli.main.synthesize_narrative")
    @patch("cli.main.classify_goal")
    @patch("cli.main.CachingClient")
    def test_cli_prints_taxonomy_tags(
        self,
        mock_client_cls,
        mock_classify,
        mock_synthesize,
        mock_enrichment,
        mock_provenance,
        mock_classification,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.return_value = (mock_enrichment, mock_provenance)
        mock_classify.return_value = mock_classification
        mock_synthesize.return_value = "Mock narrative."

        with patch(
            "sys.argv",
            ["cli", "--goal", "We want to enter AI voice", "--target-company", "Stripe"],
        ):
            main()

        captured = capsys.readouterr()
        assert "Capability tags:" in captured.out
        assert "ai/ml" in captured.out

    @patch("cli.main.synthesize_narrative")
    @patch("cli.main.classify_goal")
    @patch("cli.main.CachingClient")
    def test_cli_reports_cache_hit(
        self,
        mock_client_cls,
        mock_classify,
        mock_synthesize,
        mock_enrichment,
        mock_provenance: ApiProvenanceRecord,
        mock_classification,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_provenance.cache_hit = True
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.return_value = (mock_enrichment, mock_provenance)
        mock_classify.return_value = mock_classification
        mock_synthesize.return_value = "Mock narrative."

        with patch(
            "sys.argv",
            ["cli", "--goal", "AI voice", "--target-company", "Stripe"],
        ):
            main()

        captured = capsys.readouterr()
        assert "cache_hit=True" in captured.out

    @patch("cli.main.synthesize_narrative")
    @patch("cli.main.classify_goal")
    @patch("cli.main.CachingClient")
    def test_cli_error_propagates(
        self,
        mock_client_cls,
        mock_classify,
        mock_synthesize,
        mock_enrichment,
        mock_provenance,
        mock_classification,
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.side_effect = ValueError("Company not found: UnknownCo")
        mock_classify.return_value = mock_classification
        mock_synthesize.return_value = "Mock narrative."

        with patch(
            "sys.argv",
            ["cli", "--goal", "AI voice", "--target-company", "UnknownCo"],
        ), pytest.raises(ValueError, match="Company not found"):
            main()

    @patch("cli.main.synthesize_narrative")
    @patch("cli.main.classify_goal")
    @patch("cli.main.CachingClient")
    def test_cli_synthesize_narrative_called_with_correct_args(
        self,
        mock_client_cls,
        mock_classify,
        mock_synthesize,
        mock_enrichment,
        mock_provenance,
        mock_classification,
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.return_value = (mock_enrichment, mock_provenance)
        mock_classify.return_value = mock_classification
        mock_synthesize.return_value = "Mock narrative."

        with patch(
            "sys.argv",
            ["cli", "--goal", "We want to enter AI voice", "--target-company", "Stripe"],
        ):
            main()

        assert mock_synthesize.call_count == 1
        call_args = mock_synthesize.call_args
        evidence_breakdown = call_args[0][1]
        assert "build" in evidence_breakdown
        assert "partner" in evidence_breakdown
        assert "acquire" in evidence_breakdown
        assert call_args[0][2] == "Stripe"

    @patch("cli.main.synthesize_narrative")
    @patch("cli.main.classify_goal")
    @patch("cli.main.CachingClient")
    def test_cli_accepts_requesting_company(
        self,
        mock_client_cls,
        mock_classify,
        mock_synthesize,
        mock_enrichment,
        mock_provenance,
        mock_classification,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.return_value = (mock_enrichment, mock_provenance)
        mock_classify.return_value = mock_classification
        mock_synthesize.return_value = "Mock narrative."

        with patch(
            "sys.argv",
            [
                "cli",
                "--goal",
                "AI voice",
                "--target-company",
                "Stripe",
                "--requesting-company",
                "Acme",
            ],
        ):
            main()

        mock_client.get_company_enrichment.assert_called_once_with("Stripe")
