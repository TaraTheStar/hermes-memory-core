"""Tests for LLM implementation classes."""
import pytest
from unittest.mock import patch, MagicMock
from infrastructure.llm_implementations import LocalLLMImplementation, MockLLMInterface
from domain.core.events import LLMInfrastructureError


def _mock_config_loader(delegation_config):
    """Create a mock ConfigLoader that returns the given delegation config."""
    loader = MagicMock()
    loader.get_delegation_config.return_value = delegation_config
    return loader


def _make_impl(delegation_config, mock_openai_cls=None):
    """Create a LocalLLMImplementation with a mocked ConfigLoader and OpenAI."""
    loader = _mock_config_loader(delegation_config)
    with patch("infrastructure.llm_implementations.ConfigLoader", return_value=loader):
        if mock_openai_cls:
            with patch("infrastructure.llm_implementations.OpenAI", mock_openai_cls):
                return LocalLLMImplementation()
        return LocalLLMImplementation()


class TestLocalLLMImplementation:
    def test_init_raises_on_missing_base_url(self):
        """Should raise ValueError when base_url is missing from config."""
        with pytest.raises(ValueError, match="base_url"):
            _make_impl({"api_key": "test-key", "model": "test"})

    def test_init_raises_on_missing_api_key(self):
        """Should raise ValueError when api_key is missing from config."""
        with pytest.raises(ValueError, match="api_key"):
            _make_impl({"base_url": "http://localhost:8080", "model": "test"})

    def test_complete_returns_stripped_content(self):
        """Should return stripped content from LLM response."""
        mock_message = MagicMock()
        mock_message.content = "  hello world  "
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai = MagicMock()
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        impl = _make_impl(
            {"base_url": "http://localhost:8080", "api_key": "test-key", "model": "test"},
            mock_openai)
        result = impl.complete("test prompt")
        assert result == "hello world"

    def test_complete_raises_on_empty_choices(self):
        """Should raise LLMInfrastructureError when choices list is empty."""
        mock_response = MagicMock()
        mock_response.choices = []

        mock_openai = MagicMock()
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        impl = _make_impl(
            {"base_url": "http://localhost:8080", "api_key": "test-key", "model": "test"},
            mock_openai)
        with pytest.raises(LLMInfrastructureError):
            impl.complete("test prompt")

    def test_complete_raises_on_api_error(self):
        """Should wrap API exceptions as LLMInfrastructureError."""
        mock_openai = MagicMock()
        mock_openai.return_value.chat.completions.create.side_effect = ConnectionError("refused")

        impl = _make_impl(
            {"base_url": "http://localhost:8080", "api_key": "test-key", "model": "test"},
            mock_openai)
        with pytest.raises(LLMInfrastructureError):
            impl.complete("test prompt")

    def test_complete_with_system_prompt(self):
        """Should include system message when system_prompt is provided."""
        mock_message = MagicMock()
        mock_message.content = "response"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai = MagicMock()
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        impl = _make_impl(
            {"base_url": "http://localhost:8080", "api_key": "test-key", "model": "test"},
            mock_openai)
        impl.complete("test", system_prompt="be helpful")
        call_args = mock_openai.return_value.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "be helpful"


class TestMockLLMInterface:
    def test_keyword_audit(self):
        """Should return audit-related text for audit keywords."""
        mock = MockLLMInterface()
        result = mock.complete("Please audit this")
        assert "audit" in result.lower()

    def test_keyword_research(self):
        """Should return research-related text for research keywords."""
        mock = MockLLMInterface()
        result = mock.complete("Let's investigate this")
        assert "exploration" in result.lower() or "semantic" in result.lower()

    def test_fallback_response(self):
        """Should return a generic response when no keywords match."""
        mock = MockLLMInterface()
        result = mock.complete("something completely unrelated 12345")
        assert "synthesis" in result.lower()

    def test_multiple_keywords(self):
        """Should combine responses when multiple keywords match."""
        mock = MockLLMInterface()
        result = mock.complete("audit and research the core foundation")
        assert len(result) > 100  # Should contain multiple paragraphs
