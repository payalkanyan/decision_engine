from pathlib import Path


class LLMClient:
    """LLM API client wrapper.

    Configurable provider (default: OpenAI). Handles retries, token limits.
    Only used for goal classification and strategy synthesis — never for
    computing or adjusting numeric scores.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self._api_key = api_key
        self._model = model

    def complete(
        self, system_prompt: str, user_prompt: str, response_format: type | None = None
    ) -> str:
        """Send a completion request and return the raw text response.

        If response_format (a pydantic model) is provided, instruct the model
        to return structured JSON matching that schema.
        """
        raise NotImplementedError

    @staticmethod
    def load_prompt(filename: str) -> str:
        """Load a versioned prompt from llm/prompts/."""
        prompt_dir = Path(__file__).parent / "prompts"
        return (prompt_dir / filename).read_text()
