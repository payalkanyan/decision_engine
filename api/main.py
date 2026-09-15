import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from data.caching_client import CachingClient
from scoring.engine import analyze_strategy, get_candidates, load_rubric_yaml

app = FastAPI(
    title="Build vs Partner vs Acquire Decision Engine",
    version="1.0.0",
    description="AI-driven recommendation engine for capability acquisition strategy",
)

# Enable CORS for browser-based testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    my_company: str
    capability: str


class CandidateResponse(BaseModel):
    name: str
    score: float
    reasoning: str


class PathAnalysisResponse(BaseModel):
    path: str
    score: float
    reasoning: str
    timeline_months: int | None = None
    candidates: list[dict] = []


class AnalyzeResponse(BaseModel):
    my_company: str
    capability: str
    build_analysis: PathAnalysisResponse
    partner_analysis: PathAnalysisResponse
    acquire_analysis: PathAnalysisResponse


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/analyze-strategy", response_model=AnalyzeResponse)
def analyze_strategy_endpoint(req: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze Build vs Partner vs Acquire strategy for a company and capability.

    Args:
        my_company: Your company name (e.g. "Acme Corp")
        capability: Capability to analyze (e.g. "AI voice")

    Returns:
        Per-path analysis with scores, reasoning, and candidate lists
    """
    try:
        # 1. Fetch my company data
        caching_client = CachingClient()
        my_company_data, _ = caching_client.get_company_enrichment(req.my_company)

        # Jobs/headcount are optional — degrade gracefully if the API lacks access
        try:
            my_company_jobs, _ = caching_client.get_jobs(req.my_company)
        except Exception:
            my_company_jobs = None
        try:
            my_company_headcount, _ = caching_client.get_headcount_timeseries(req.my_company)
        except Exception:
            my_company_headcount = None

        # 2. Get candidates for each path (optional — degrade gracefully)
        try:
            build_candidates = get_candidates(caching_client, req.capability, "build")
        except Exception:
            build_candidates = []
        try:
            partner_candidates = get_candidates(caching_client, req.capability, "partner")
        except Exception:
            partner_candidates = []
        try:
            acquire_candidates = get_candidates(caching_client, req.capability, "acquire")
        except Exception:
            acquire_candidates = []

        # 3. Run strategy analysis with per-path candidates
        rubric = load_rubric_yaml("rubric.yaml")
        analysis = analyze_strategy(
            my_company=req.my_company,
            capability=req.capability,
            my_company_enrichment=my_company_data,
            my_company_jobs=my_company_jobs,
            my_company_headcount=my_company_headcount,
            candidates=partner_candidates or acquire_candidates or build_candidates,
            rubric=rubric,
        )

        # 4. Build response
        return AnalyzeResponse(
            my_company=req.my_company,
            capability=req.capability,
            build_analysis=PathAnalysisResponse(
                path="build",
                score=analysis.build_analysis.score,
                reasoning=analysis.build_analysis.reasoning,
                timeline_months=analysis.build_analysis.timeline_months,
            ),
            partner_analysis=PathAnalysisResponse(
                path="partner",
                score=analysis.partner_analysis.score,
                reasoning=analysis.partner_analysis.reasoning,
                candidates=[
                    {
                        "name": c.name,
                        "score": c.score,
                        "reasoning": c.reasoning,
                    }
                    for c in analysis.partner_analysis.candidates
                ],
            ),
            acquire_analysis=PathAnalysisResponse(
                path="acquire",
                score=analysis.acquire_analysis.score,
                reasoning=analysis.acquire_analysis.reasoning,
                candidates=[
                    {
                        "name": c.name,
                        "score": c.score,
                        "reasoning": c.reasoning,
                    }
                    for c in analysis.acquire_analysis.candidates
                ],
            ),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
