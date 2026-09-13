from llm.schemas import StrategyNarrative
from scoring.schemas import CandidateCompany, PathScore, ProvenanceRecord, Recommendation


def synthesize_strategy(
    path_scores: list[PathScore],
    recommendation: Recommendation,
    evidence_trail: list[ProvenanceRecord],
    candidate_companies: list[CandidateCompany],
    llm_api_key: str,
) -> StrategyNarrative:
    """Turn scored evidence into a written strategy narrative.

    Uses prompts/synthesize_strategy_v1.md. The LLM narrates the
    recommendation, trade-offs, and risks from scores that /scoring
    already produced. It never computes or adjusts numeric scores.
    """
    raise NotImplementedError
