import json

from llm.client import GroqClient
from llm.schemas import GoalClassification
from scoring.schemas import PathScore


def _default_client() -> GroqClient:
    return GroqClient()


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
    response = client.complete(system, user)
    parsed = json.loads(response)

    return GoalClassification(
        goal=goal,
        taxonomy_tags=parsed.get("taxonomy_tags", []),
        search_keywords=parsed.get("search_keywords", []),
        build_signals=parsed.get("build_signals", []),
        partner_signals=parsed.get("partner_signals", []),
        acquire_signals=parsed.get("acquire_signals", []),
    )


def synthesize_narrative(
    path_score: PathScore,
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
