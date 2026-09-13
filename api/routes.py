from fastapi import APIRouter
from pydantic import BaseModel

from scoring.schemas import AnalysisOutput

router = APIRouter()


class AnalyzeRequest(BaseModel):
    goal: str
    company_name: str | None = None
    dry_run: bool = False


class AnalyzeResponse(BaseModel):
    output: AnalysisOutput
    narrative: str | None = None


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze a goal and return a Build/Partner/Acquire recommendation."""
    raise NotImplementedError
