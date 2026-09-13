from llm.schemas import GoalClassification


def classify_goal(goal: str, llm_api_key: str) -> GoalClassification:
    """Turn a free-text goal into a capability taxonomy.

    Uses prompts/classify_goal_v1.md. The LLM extracts taxonomy tags,
    search keywords, and signal descriptors from the goal — it does not
    compute any scores.
    """
    raise NotImplementedError
