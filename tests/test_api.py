"""Tests for api/main.py — the FastAPI application.

All external dependencies (CachingClient, LLM) are mocked. The scoring
engine runs against the real rubric.yaml and mock enrichment data.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from data.caching_client import ApiProvenanceRecord
from data.schemas import (
    CompanyEnrichment,
    CompanyEnrichmentResponse,
    FundingSummary,
    Technographics,
)
from llm.schemas import GoalClassification

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


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
                categories=["Cloud Infrastructure", "Developer Tools"],
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


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestHealth:
    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAnalyzeStrategy:
    @patch("api.main.get_candidates")
    @patch("api.main.CachingClient")
    def test_analyze_strategy_success(
        self,
        mock_client_cls,
        mock_get_candidates,
        mock_enrichment: CompanyEnrichmentResponse,
        mock_provenance: ApiProvenanceRecord,
        mock_candidates: list[CompanyEnrichmentResponse],
        client: TestClient,
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.return_value = (
            mock_enrichment,
            mock_provenance,
        )
        mock_get_candidates.return_value = mock_candidates

        response = client.post(
            "/analyze-strategy",
            json={"my_company": "Acme", "capability": "AI voice"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["my_company"] == "Acme"
        assert data["capability"] == "AI voice"
        assert "build_analysis" in data
        assert "partner_analysis" in data
        assert "acquire_analysis" in data

        # Build analysis
        assert "score" in data["build_analysis"]
        assert "reasoning" in data["build_analysis"]
        assert "timeline_months" in data["build_analysis"]
        assert "estimated_cost_usd" in data["build_analysis"]

        # Partner analysis
        assert "score" in data["partner_analysis"]
        assert "reasoning" in data["partner_analysis"]
        assert "candidates" in data["partner_analysis"]

        # Acquire analysis
        assert "score" in data["acquire_analysis"]
        assert "reasoning" in data["acquire_analysis"]
        assert "candidates" in data["acquire_analysis"]

    @patch("api.main.get_candidates")
    @patch("api.main.CachingClient")
    def test_analyze_strategy_caching_client_called(
        self,
        mock_client_cls,
        mock_get_candidates,
        mock_enrichment: CompanyEnrichmentResponse,
        mock_provenance: ApiProvenanceRecord,
        mock_candidates: list[CompanyEnrichmentResponse],
        client: TestClient,
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.return_value = (
            mock_enrichment,
            mock_provenance,
        )
        mock_get_candidates.return_value = mock_candidates

        client.post(
            "/analyze-strategy",
            json={"my_company": "Acme", "capability": "AI voice"},
        )

        mock_client.get_company_enrichment.assert_called_with("Acme")

    @patch("api.main.get_candidates")
    @patch("api.main.CachingClient")
    def test_analyze_strategy_candidates_ranked_by_score(
        self,
        mock_client_cls,
        mock_get_candidates,
        mock_enrichment: CompanyEnrichmentResponse,
        mock_provenance: ApiProvenanceRecord,
        mock_candidates: list[CompanyEnrichmentResponse],
        client: TestClient,
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.return_value = (
            mock_enrichment,
            mock_provenance,
        )
        mock_get_candidates.return_value = mock_candidates

        response = client.post(
            "/analyze-strategy",
            json={"my_company": "Acme", "capability": "AI voice"},
        )

        data = response.json()
        # Candidates should be sorted by score descending
        partner_candidates = data["partner_analysis"]["candidates"]
        acquire_candidates = data["acquire_analysis"]["candidates"]

        for candidates in [partner_candidates, acquire_candidates]:
            scores = [c["score"] for c in candidates]
            assert scores == sorted(scores, reverse=True)

    @patch("api.main.get_candidates")
    @patch("api.main.CachingClient")
    def test_analyze_strategy_server_error_on_missing_company(
        self,
        mock_client_cls,
        mock_get_candidates,
        mock_enrichment: CompanyEnrichmentResponse,
        mock_provenance: ApiProvenanceRecord,
        mock_candidates: list[CompanyEnrichmentResponse],
        client: TestClient,
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.side_effect = ValueError(
            "Company not found"
        )
        mock_get_candidates.return_value = mock_candidates

        response = client.post(
            "/analyze-strategy",
            json={"my_company": "UnknownCo", "capability": "AI voice"},
        )

        assert response.status_code == 500
        assert "Company not found" in response.json()["detail"]


class TestAnalyzeStrategyValidation:
    def test_analyze_strategy_missing_my_company_returns_422(
        self,
        client: TestClient,
    ) -> None:
        response = client.post("/analyze-strategy", json={"capability": "AI voice"})
        assert response.status_code == 422

    def test_analyze_strategy_missing_capability_returns_422(
        self,
        client: TestClient,
    ) -> None:
        response = client.post("/analyze-strategy", json={"my_company": "Acme"})
        assert response.status_code == 422

    def test_analyze_strategy_invalid_json_returns_400(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            "/analyze-strategy",
            content="{invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in (400, 422)