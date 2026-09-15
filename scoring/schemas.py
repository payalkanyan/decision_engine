from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from data.provenance import ProvenanceRecord

# ── Rubric models (loaded from rubric.yaml) ─────────────────────


class Criterion(BaseModel):
    id: str
    description: str
    source: str
    weight: float
    scale: str


class Path(BaseModel):
    description: str
    weight_in_final_decision: float
    criteria: list[Criterion]


class Rubric(BaseModel):
    version: float
    capability_goal: dict  # description + taxonomy_tags
    paths: dict[str, Path]  # "build", "partner", "acquire"


# ── Scoring output models ───────────────────────────────────────


class CriterionScore(BaseModel):
    criterion_id: str
    score: float  # 0-10
    weight: float  # from rubric (post-renormalization if applicable)
    evidence: ProvenanceRecord | None = None
    excluded: bool = False  # True if data was missing → renormalized out
    notes: str | None = None


class PathScore(BaseModel):
    path: Literal["build", "partner", "acquire"]
    score: float  # 0-10 weighted sum
    weight_in_final_decision: float
    criteria: list[CriterionScore] = []


# ── Final output (matches rubric.yaml output_format) ────────────


class CandidateDecisionMaker(BaseModel):
    name: str
    title: str
    source: str = "decision_makers_filter"


class CandidateCompany(BaseModel):
    name: str
    path_relevance: Literal["build", "partner", "acquire"]
    key_signals: list[str] = []
    decision_makers: list[CandidateDecisionMaker] = []


class CandidateWithScore(CandidateCompany):
    score: float = 0.0
    reasoning: str = ""


class Recommendation(BaseModel):
    primary_path: Literal["build", "partner", "acquire"]
    is_close_call: bool = False
    close_call_alternative: Literal["build", "partner", "acquire"] | None = None
    rationale: str


class AnalysisOutput(BaseModel):
    """The top-level output object. Matches rubric.yaml output_format."""

    final_scores: dict[str, float]  # {"build": 7.2, "partner": 5.1, "acquire": 6.8}
    recommendation: Recommendation
    evidence_trail: list[ProvenanceRecord] = []
    candidate_companies: list[CandidateCompany] = []
    assumptions_and_gaps: list[str] = []  # explicit list of missing/stale/estimated data
    generated_at: datetime


# ── New per-path analysis models ────────────────────────────────


class BuildAnalysis(BaseModel):
    path: Literal["build"] = "build"
    score: float
    reasoning: str
    timeline_months: int
    candidates: list = []


class PartnerAnalysis(BaseModel):
    path: Literal["partner"] = "partner"
    score: float
    reasoning: str
    candidates: list[CandidateWithScore] = []


class AcquireAnalysis(BaseModel):
    path: Literal["acquire"] = "acquire"
    score: float
    reasoning: str
    candidates: list[CandidateWithScore] = []


class StrategyAnalysis(BaseModel):
    my_company: str
    capability: str
    build_analysis: BuildAnalysis
    partner_analysis: PartnerAnalysis
    acquire_analysis: AcquireAnalysis
