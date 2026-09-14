import json
from unittest.mock import MagicMock, patch

import groq
import pytest
from groq import RateLimitError

from llm.client import GroqClient
from llm.schemas import GoalClassification
from llm.synthesize import classify_goal, synthesize_narrative
from scoring.schemas import PathScore


def _mock_groq_response(content: str):
    """Build a mock response object mimicking groq.ChatCompletion."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    return response


class TestGroqClient:
    @patch("llm.client.groq.Groq")
    def test_init_reads_api_key_from_env(self, mock_groq_cls):
        with patch.dict("os.environ", {"GROQ_API_KEY": "env-key-123"}):
            GroqClient()
            mock_groq_cls.assert_called_once_with(api_key="env-key-123")

    @patch("llm.client.groq.Groq")
    def test_init_uses_passed_api_key(self, mock_groq_cls):
        GroqClient(api_key="explicit-key")
        mock_groq_cls.assert_called_once_with(api_key="explicit-key")

    @patch("llm.client.groq.Groq")
    def test_complete_returns_content(self, mock_groq_cls):
        mock_client = mock_groq_cls.return_value
        mock_client.chat.completions.create.return_value = _mock_groq_response(
            "Hello world"
        )

        client = GroqClient(api_key="test-key")
        result = client.complete("sys prompt", "user prompt")

        assert result == "Hello world"
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "groq/compound-mini"
        assert call_kwargs.kwargs["temperature"] == 0.3
        assert call_kwargs.kwargs["max_tokens"] == 500
        assert call_kwargs.kwargs["messages"][0]["role"] == "system"
        assert call_kwargs.kwargs["messages"][1]["role"] == "user"

    @patch("llm.client.groq.Groq")
    def test_complete_with_response_format_sets_json_object(self, mock_groq_cls):
        mock_client = mock_groq_cls.return_value
        mock_client.chat.completions.create.return_value = _mock_groq_response("{}")

        client = GroqClient(api_key="test-key")
        client.complete("sys", "user", response_format=GoalClassification)

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["response_format"] == {"type": "json_object"}

    @patch("llm.client.groq.Groq")
    @patch("llm.client.time.sleep")
    def test_retry_on_429_then_succeeds(self, mock_sleep, mock_groq_cls):
        mock_client = mock_groq_cls.return_value

        rate_limit_error = RateLimitError(
            message="rate limited",
            response=MagicMock(status_code=429),
            body={},
        )

        mock_client.chat.completions.create.side_effect = [
            rate_limit_error,
            _mock_groq_response("Success after retry"),
        ]

        client = GroqClient(api_key="test-key")
        result = client.complete("sys", "user")

        assert result == "Success after retry"
        assert mock_client.chat.completions.create.call_count == 2
        assert mock_sleep.call_count == 1
        assert mock_sleep.call_args[0][0] == 1.0

    @patch("llm.client.groq.Groq")
    @patch("llm.client.time.sleep")
    def test_retry_backoff_exponential(self, mock_sleep, mock_groq_cls):
        mock_client = mock_groq_cls.return_value

        error = RateLimitError(
            message="rate limited",
            response=MagicMock(status_code=429),
            body={},
        )

        mock_client.chat.completions.create.side_effect = [error, error, error, error]

        client = GroqClient(api_key="test-key")
        with pytest.raises(RateLimitError):
            client.complete("sys", "user")

        assert mock_client.chat.completions.create.call_count == 4
        assert mock_sleep.call_count == 3
        assert mock_sleep.call_args_list[0][0][0] == 1.0
        assert mock_sleep.call_args_list[1][0][0] == 2.0
        assert mock_sleep.call_args_list[2][0][0] == 4.0

    @patch("llm.client.groq.Groq")
    @patch("llm.client.time.sleep")
    def test_retry_on_5xx_then_succeeds(self, mock_sleep, mock_groq_cls):
        mock_client = mock_groq_cls.return_value

        server_error = groq.APIStatusError(
            message="Internal Server Error",
            response=MagicMock(status_code=500),
            body={},
        )

        mock_client.chat.completions.create.side_effect = [
            server_error,
            _mock_groq_response("Recovered from 5xx"),
        ]

        client = GroqClient(api_key="test-key")
        result = client.complete("sys", "user")

        assert result == "Recovered from 5xx"
        assert mock_sleep.call_count == 1


class TestClassifyGoal:
    @patch("llm.synthesize._default_client")
    def test_classify_goal_returns_goal_classification(self, mock_default):
        mock_client = mock_default.return_value
        mock_response = json.dumps(
            {
                "taxonomy_tags": ["speech-to-text", "voice-agents"],
                "search_keywords": ["voice AI", "speech recognition"],
                "build_signals": ["existing NLP team", "audio pipeline"],
                "partner_signals": ["voice API providers"],
                "acquire_signals": ["voice AI startups"],
            }
        )
        mock_client.complete.return_value = mock_response

        result = classify_goal("We want to enter AI voice")

        assert isinstance(result, GoalClassification)
        assert result.goal == "We want to enter AI voice"
        assert "speech-to-text" in result.taxonomy_tags
        assert "voice-agents" in result.taxonomy_tags
        assert "voice AI" in result.search_keywords
        mock_client.complete.assert_called_once()

    @patch("llm.synthesize._default_client")
    def test_classify_goal_handles_minimal_response(self, mock_default):
        mock_client = mock_default.return_value
        mock_client.complete.return_value = json.dumps({"taxonomy_tags": ["tts"]})

        result = classify_goal("Build text-to-speech")

        assert isinstance(result, GoalClassification)
        assert result.taxonomy_tags == ["tts"]
        assert result.search_keywords == []
        assert result.build_signals == []


class TestSynthesizeNarrative:
    @patch("llm.synthesize._default_client")
    def test_synthesize_narrative_returns_string(self, mock_default):
        target_company = "Acme Corp"
        expected = (
            "Acme Corp should pursue the acquire path with a score of 8.5/10, "
            "based on strong funding signals and relevant talent density."
        )
        mock_client = mock_default.return_value
        mock_client.complete.return_value = expected

        path_score = PathScore(path="acquire", score=8.5, weight_in_final_decision=1.0)
        evidence = {"funding": "$50M raised", "headcount": "150 engineers"}

        result = synthesize_narrative(path_score, evidence, target_company)

        assert isinstance(result, str)
        assert len(result) > 50
        assert "acquire" in result.lower()
        assert target_company in result
        mock_client.complete.assert_called_once()

    @patch("llm.synthesize._default_client")
    def test_synthesize_narrative_default_target(self, mock_default):
        mock_client = mock_default.return_value
        mock_client.complete.return_value = (
            "The target company should acquire to reach AI voice capabilities "
            "and capture the market opportunity."
        )

        path_score = PathScore(path="acquire", score=8.5, weight_in_final_decision=1.0)
        evidence = {"funding": "$50M"}

        result = synthesize_narrative(path_score, evidence)

        assert isinstance(result, str)
        assert len(result) > 50
        mock_client.complete.assert_called_once()

    @patch("llm.synthesize._default_client")
    def test_synthesize_narrative_includes_score_and_evidence(self, mock_default):
        mock_client = mock_default.return_value
        mock_client.complete.return_value = (
            "Build path scores 7.2/10. Evidence shows mature engineering team."
        )

        path_score = PathScore(path="build", score=7.2, weight_in_final_decision=1.0)
        evidence = {"engineering": "50 senior engineers", "patents": "12 AI patents"}

        synthesize_narrative(path_score, evidence, "DataCorp")

        call_args = mock_client.complete.call_args
        user_prompt = call_args[0][1]
        assert "7.2" in user_prompt
        assert "build" in user_prompt
        assert "DataCorp" in user_prompt
