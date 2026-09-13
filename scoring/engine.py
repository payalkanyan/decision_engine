from scoring.schemas import AnalysisOutput, PathScore, Rubric


def score_path(
    path_name: str,
    rubric: Rubric,
    evidence: dict,
) -> PathScore:
    """Score a single path (build/partner/acquire) using the rubric.

    Iterates criteria, calls the matching criterion scoring function,
    handles weight renormalization when data is missing (never defaults
    to 0 or 5).
    """
    raise NotImplementedError


def score_all(
    rubric: Rubric,
    evidence: dict,
) -> list[PathScore]:
    """Score all three paths and return them in rubric order."""
    raise NotImplementedError


def build_output(
    path_scores: list[PathScore],
    rubric: Rubric,
    candidate_companies: list | None = None,
    assumptions_and_gaps: list[str] | None = None,
) -> AnalysisOutput:
    """Assemble the final AnalysisOutput from path scores.

    Determines the recommendation: highest scoring path, or "close call"
    if the top two scores are within 1.0 of each other.
    """
    raise NotImplementedError
