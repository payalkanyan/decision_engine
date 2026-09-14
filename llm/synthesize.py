import json
import re

from llm.client import GroqClient
from llm.schemas import GoalClassification
from scoring.schemas import CandidateWithScore, PathScore


def _default_client() -> GroqClient:
    return GroqClient()


def _extract_json(response: str) -> dict:
    """Extract a JSON dict from an LLM response.

    Some reasoning models return explanatory text before the JSON, or wrap
    it in markdown code blocks. This tries direct parse first, then
    falls back to extracting from ```json blocks or any {…} object.
    """
    # Try direct JSON parse first
    try:
        result = json.loads(response)
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, TypeError):
        pass

    # Try to find JSON inside a markdown code block
    match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Fall back to finding any top-level JSON object
    match = re.search(r"\{[\s\S]*\}", response)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from response: {response[:200]}")


def classify_goal(goal: str) -> GoalClassification:
    """Turn a free-text goal into a capability taxonomy.

    Uses prompts/classify_goal_v1.md. The LLM extracts taxonomy tags,
    search keywords, and signal descriptors from the goal — it does not
    compute any scores.
    """
    system = (
        "You are a capability analyst. Given a strategic goal, extract: "
        "taxonomy_tags, search_keywords, build_signals, partner_signals, "
        "and acquire_signals. Return JSON matching the GoalClassification schema."
    )
    user = (
        f"Goal: {goal}\n\n"
        'Return JSON: {"taxonomy_tags": [...], "search_keywords": [...], '
        '"build_signals": [...], "partner_signals": [...], "acquire_signals": [...]}'
    )

    client = _default_client()
    response = client.complete(system, user, response_format=GoalClassification)
    parsed = _extract_json(response)

    return GoalClassification(
        goal=goal,
        taxonomy_tags=parsed.get("taxonomy_tags", []),
        search_keywords=parsed.get("search_keywords", []),
        build_signals=parsed.get("build_signals", []),
        partner_signals=parsed.get("partner_signals", []),
        acquire_signals=parsed.get("acquire_signals", []),
    )


def synthesize_narrative(
    path_score: PathScore | None,
    evidence_breakdown: dict,
    target_company: str = "target",
) -> str:
    """Write a 2-3 sentence strategic recommendation from a scored path.

    Uses the Groq LLM to narrate from scores that /scoring already produced.
    It never computes or adjusts numeric scores.
    """
    system = "You write 2-3 sentence strategic recommendations based on analysis. Be specific."
    user = (
        f"Recommendation: {path_score.path}\n"
        f"Score: {path_score.score}/10\n"
        f"Evidence: {evidence_breakdown}\n"
        f"Target: {target_company}\n\n"
        "Write a 2-3 sentence recommendation citing specific numbers and evidence."
    )

    client = _default_client()
    response = client.complete(system, user)
    return response


def synthesize_build_reasoning(my_company: str, score: float) -> str:
    """Generate reasoning for the build path."""
    return (
        f"{my_company} has a build score of {score:.1f}/10. "
        f"Building in-house provides full control over the capability "
        f"but requires significant investment in talent and infrastructure."
    )


def synthesize_partner_reasoning(candidates: list[CandidateWithScore], score: float) -> str:
    """Generate reasoning for the partner path."""
    top = candidates[0].name if candidates else "no candidates"
    return (
        f"Partner path scored {score:.1f}/10. Top candidate: {top}. "
        f"Partnership reduces time-to-market vs building from scratch."
    )


def synthesize_acquire_reasoning(candidates: list[CandidateWithScore], score: float) -> str:
    """Generate reasoning for the acquire path."""
    top = candidates[0].name if candidates else "no candidates"
    return (
        f"Acquire path scored {score:.1f}/10. Top target: {top}. "
        f"Acquisition provides fastest path to capability with existing team."
    )
