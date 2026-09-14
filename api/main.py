import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from data.caching_client import CachingClient
from llm.synthesize import classify_goal, synthesize_narrative
from scoring.engine import Evidence, build_output, score_all
from scoring.rubric_loader import load_rubric

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


class RecommendationRequest(BaseModel):
    goal: str
    target_company: str
    requesting_company: str | None = None


class RecommendationResponse(BaseModel):
    goal: str
    target_company: str
    path: str
    score: float
    is_close_call: bool
    narrative: str
    criteria_breakdown: dict[str, float]


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(req: RecommendationRequest) -> RecommendationResponse:
    """Get a Build/Partner/Acquire recommendation for a target company and goal.

    Args:
        goal: Strategic capability goal (e.g. "We want to enter AI voice")
        target_company: Target company name (e.g. "Stripe")
        requesting_company: Your company name (optional)

    Returns:
        Recommendation with path, score, narrative, and evidence breakdown
    """
    try:
        # 1. Classify goal
        classification = classify_goal(req.goal)

        # 2. Fetch target company data
        caching_client = CachingClient()
        target_data, provenance = caching_client.get_company_enrichment(
            req.target_company
        )

        # 3. Build evidence and score all 3 paths
        rubric = load_rubric("rubric.yaml")
        evidence = Evidence(
            taxonomy_tags=classification.taxonomy_tags,
            own_enrichment=target_data,
            candidate_enrichment=target_data,
            acquire_enrichment=target_data,
            api_call_ids={
                "own_enrichment": provenance.api_call_id,
                "candidate_enrichment": provenance.api_call_id,
                "acquire_enrichment": provenance.api_call_id,
            },
        )

        # 4. Score all 3 paths
        scores = score_all(rubric, evidence)

        # 5. Build output
        output = build_output(scores, rubric)

        # 6. Generate narrative
        top_path = output.recommendation.primary_path
        top_path_score = next(s for s in scores if s.path == top_path)
        narrative = synthesize_narrative(
            top_path_score,
            output.final_scores,
            req.target_company,
        )

        # 7. Build response
        return RecommendationResponse(
            goal=req.goal,
            target_company=req.target_company,
            path=top_path,
            score=round(top_path_score.score, 1),
            is_close_call=output.recommendation.is_close_call,
            narrative=narrative,
            criteria_breakdown={
                c.criterion_id: round(c.score, 1) for c in top_path_score.criteria
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
