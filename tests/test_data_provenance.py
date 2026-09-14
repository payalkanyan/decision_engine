import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx

from data.client import CrustdataClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"
BASE_URL = "https://api.crustdata.com"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


@pytest.fixture(autouse=True)
def _api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CRUSTDATA_API_KEY", "test-api-key")


def make_client() -> CrustdataClient:
    return CrustdataClient(api_key="test-api-key", base_url=BASE_URL)


# ── Successful calls ─────────────────────────────────────────────


@respx.mock
def test_get_company_enrichment_parses_response() -> None:
    route = respx.post(f"{BASE_URL}/company/enrich").mock(
        return_value=httpx.Response(200, json=load_fixture("company_enrichment.json")),
    )

    result = make_client().get_company_enrichment("TechCorp Inc")

    assert route.called
    assert route.call_count == 1
    assert result.company.company_name == "TechCorp Inc"
    assert result.company.employee_count == 500
    assert result.company.technographics.technologies == [
        "Software Development",
        "Enterprise Software",
        "Information Services",
    ]


@respx.mock
def test_get_company_enrichment_sends_name_param() -> None:
    route = respx.post(f"{BASE_URL}/company/enrich").mock(
        return_value=httpx.Response(200, json=load_fixture("company_enrichment.json")),
    )

    make_client().get_company_enrichment("TechCorp Inc")

    request = route.calls.last.request
    body = json.loads(request.content)
    assert body["names"] == ["TechCorp Inc"]


@respx.mock
def test_search_companies_posts_json_body() -> None:
    route = respx.post(f"{BASE_URL}/company/search").mock(
        return_value=httpx.Response(200, json=load_fixture("company_search.json")),
    )

    filters = {"industry": "AI/ML", "max_employees": 50}
    result = make_client().search_companies(filters)

    assert route.called
    assert result.total_count == 2
    assert result.results[0].name == "VoiceAI Labs"

    request = route.calls.last.request
    assert json.loads(request.content) == filters


@respx.mock
def test_get_web_traffic_parses_response() -> None:
    route = respx.get(f"{BASE_URL}/web/traffic").mock(
        return_value=httpx.Response(200, json=load_fixture("web_traffic.json")),
    )

    result = make_client().get_web_traffic("voiceailabs.com")

    assert route.called
    assert result.domain == "voiceailabs.com"
    assert len(result.series) == 3
    assert result.series[0].monthly_visits == 45000


@respx.mock
def test_sends_bearer_auth_header() -> None:
    route = respx.get(f"{BASE_URL}/web/traffic").mock(
        return_value=httpx.Response(200, json=load_fixture("web_traffic.json")),
    )

    make_client().get_web_traffic("example.com")

    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer test-api-key"


# ── Retry behavior ───────────────────────────────────────────────


@respx.mock
def test_retries_on_429_then_succeeds() -> None:
    route = respx.post(f"{BASE_URL}/company/enrich").mock(
        side_effect=[
            httpx.Response(429, headers={"retry-after": "0"}),
            httpx.Response(200, json=load_fixture("company_enrichment.json")),
        ]
    )

    with patch("data.client.time.sleep"):
        result = make_client().get_company_enrichment("TechCorp Inc")

    assert route.call_count == 2
    assert result.company.company_name == "TechCorp Inc"


@respx.mock
def test_retries_on_500_then_succeeds() -> None:
    route = respx.post(f"{BASE_URL}/company/enrich").mock(
        side_effect=[
            httpx.Response(500),
            httpx.Response(502),
            httpx.Response(200, json=load_fixture("company_enrichment.json")),
        ]
    )

    with patch("data.client.time.sleep"):
        result = make_client().get_company_enrichment("TechCorp Inc")

    assert route.call_count == 3
    assert result.company.company_name == "TechCorp Inc"


@respx.mock
def test_raises_after_max_retries_exhausted() -> None:
    route = respx.post(f"{BASE_URL}/company/enrich").mock(
        return_value=httpx.Response(500),
    )

    with patch("data.client.time.sleep"), pytest.raises(httpx.HTTPStatusError):
        make_client().get_company_enrichment("TechCorp Inc")

    assert route.call_count == 3


@respx.mock
def test_does_not_retry_on_404() -> None:
    route = respx.post(f"{BASE_URL}/company/enrich").mock(
        return_value=httpx.Response(404),
    )

    with pytest.raises(httpx.HTTPStatusError):
        make_client().get_company_enrichment("Does Not Exist")

    assert route.call_count == 1
