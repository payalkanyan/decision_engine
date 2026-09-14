"""Tests for api/main.py — the FastAPI application.

All external dependencies (CachingClient, LLM) are mocked. The scoring
engine runs against the real rubric.yaml and mock enrichment data.
"""

from datetime import UTC, datetime
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


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestHealth:
    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestRecommend:
    @patch("api.main.synthesize_narrative")
    @patch("api.main.classify_goal")
    @patch("api.main.CachingClient")
    def test_recommend_success(
        self,
        mock_client_cls,
        mock_classify,
        mock_synthesize,
        mock_enrichment: CompanyEnrichmentResponse,
        mock_provenance: ApiProvenanceRecord,
        mock_classification: GoalClassification,
        client: TestClient,
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.return_value = (mock_enrichment, mock_provenance)
        mock_classify.return_value = mock_classification
        mock_synthesize.return_value = "Mock narrative for Stripe."

        response = client.post(
            "/recommend",
            json={"goal": "We want to enter AI voice", "target_company": "Stripe"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["goal"] == "We want to enter AI voice"
        assert data["target_company"] == "Stripe"
        assert data["path"] in ["build", "partner", "acquire"]
        assert isinstance(data["score"], float)
        assert 0 <= data["score"] <= 10
        assert isinstance(data["is_close_call"], bool)
        assert isinstance(data["narrative"], str)
        assert len(data["narrative"]) > 0
        assert isinstance(data["criteria_breakdown"], dict)
        assert len(data["criteria_breakdown"]) > 0

    @patch("api.main.synthesize_narrative")
    @patch("api.main.classify_goal")
    @patch("api.main.CachingClient")
    def test_recommend_response_has_required_fields(
        self,
        mock_client_cls,
        mock_classify,
        mock_synthesize,
        mock_enrichment,
        mock_provenance,
        mock_classification,
        client: TestClient,
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.return_value = (mock_enrichment, mock_provenance)
        mock_classify.return_value = mock_classification
        mock_synthesize.return_value = "Strategy: go acquire them."

        response = client.post(
            "/recommend",
            json={"goal": "We want to enter AI voice", "target_company": "Stripe"},
        )

        data = response.json()
        required_fields = {
            "goal",
            "target_company",
            "path",
            "score",
            "is_close_call",
            "narrative",
            "criteria_breakdown",
        }
        assert required_fields.issubset(data.keys())

    @patch("api.main.synthesize_narrative")
    @patch("api.main.classify_goal")
    @patch("api.main.CachingClient")
    def test_recommend_caching_client_called_with_target(
        self,
        mock_client_cls,
        mock_classify,
        mock_synthesize,
        mock_enrichment,
        mock_provenance,
        mock_classification,
        client: TestClient,
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.return_value = (mock_enrichment, mock_provenance)
        mock_classify.return_value = mock_classification
        mock_synthesize.return_value = "Narrative."

        client.post(
            "/recommend",
            json={"goal": "AI voice", "target_company": "Stripe"},
        )

        mock_client.get_company_enrichment.assert_called_once_with("Stripe")

    @patch("api.main.synthesize_narrative")
    @patch("api.main.classify_goal")
    @patch("api.main.CachingClient")
    def test_recommend_server_error_on_missing_company(
        self,
        mock_client_cls,
        mock_classify,
        mock_synthesize,
        mock_enrichment,
        mock_provenance,
        mock_classification,
        client: TestClient,
    ) -> None:
        mock_client = mock_client_cls.return_value
        mock_client.get_company_enrichment.side_effect = ValueError("Company not found")
        mock_classify.return_value = mock_classification
        mock_synthesize.return_value = "Narrative."

        response = client.post(
            "/recommend",
            json={"goal": "AI voice", "target_company": "UnknownCo"},
        )

        assert response.status_code == 500
        assert "Company not found" in response.json()["detail"]


class TestRecommendValidation:
    def test_recommend_missing_target_company_returns_422(
        self,
        client: TestClient,
    ) -> None:
        response = client.post("/recommend", json={"goal": "We want to enter AI voice"})
        assert response.status_code == 422

    def test_recommend_missing_goal_returns_422(self, client: TestClient) -> None:
        response = client.post("/recommend", json={"target_company": "Stripe"})
        assert response.status_code == 422

    def test_recommend_invalid_json_returns_400(self, client: TestClient) -> None:
        response = client.post(
            "/recommend",
            content="{invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in (400, 422)

    def test_recommend_missing_requesting_company_defaults_none(
        self,
        mock_enrichment: CompanyEnrichmentResponse,
        mock_provenance: ApiProvenanceRecord,
        mock_classification: GoalClassification,
        client: TestClient,
    ) -> None:
        with patch("api.main.CachingClient") as mock_client_cls, \
             patch("api.main.classify_goal", return_value=mock_classification), \
             patch("api.main.synthesize_narrative", return_value="Narrative."):
            mock_client = mock_client_cls.return_value
            mock_client.get_company_enrichment.return_value = (mock_enrichment, mock_provenance)

            response = client.post(
                "/recommend",
                json={"goal": "AI voice", "target_company": "Stripe"},
            )

        assert response.status_code == 200
