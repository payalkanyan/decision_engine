import os
import time

import groq
from pydantic import BaseModel


class GroqClient:
    """Groq API client wrapper with retry-with-backoff.

    Only used for goal classification and strategy synthesis — never for
    computing or adjusting numeric scores.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ["GROQ_API_KEY"]
        self._client = groq.Groq(api_key=self._api_key)

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: type[BaseModel] | None = None,
    ) -> str | dict:
        """Send a completion request with retry-with-backoff on 429/5xx.

        Retries up to 3 times with exponential backoff (1s, 2s, 4s).
        """
        max_retries = 3
        backoff = 1.0

        for attempt in range(max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model="groq/compound-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=500,
                    response_format=(
                        {"type": "json_object"} if response_format else None
                    ),
                )
                return response.choices[0].message.content
            except groq.RateLimitError:
                if attempt == max_retries:
                    raise
                time.sleep(backoff)
                backoff *= 2
            except groq.APIStatusError as e:
                if e.status_code < 500 or attempt == max_retries:
                    raise
                time.sleep(backoff)
                backoff *= 2
