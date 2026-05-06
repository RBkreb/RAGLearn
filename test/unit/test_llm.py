"""Unit tests for src/models/llm.py"""

from unittest.mock import MagicMock, patch

import pytest

from src.config import LlamaCppConfig
from src.exceptions import EmbeddingError
from src.models.llm import LlamaCppLLMWrapper, create_llm


class TestLlamaCppLLMWrapperInit:
    """Tests for LlamaCppLLMWrapper.__init__."""

    def test_init_creates_chat_llamacpp_with_correct_config(self) -> None:
        """Verify __init__ creates ChatLlamaCpp with correct configuration."""
        config = LlamaCppConfig(
            model_path="./model/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q6_K.gguf",
            temperature=0.1,
            n_ctx=2048,
            n_gpu_layers=-1,
            timeout=120,
        )

        with patch("src.models.llm.ChatLlamaCpp") as mock_chat_llamacpp:
            mock_instance = MagicMock()
            mock_chat_llamacpp.return_value = mock_instance

            wrapper = LlamaCppLLMWrapper(config)

            mock_chat_llamacpp.assert_called_once_with(
                model_path="./model/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q6_K.gguf",
                temperature=0.1,
                n_ctx=2048,
                n_gpu_layers=-1,
                verbose=False,
                max_tokens=2048,
            )
            assert wrapper.config == config
            assert wrapper._model is mock_instance

    def test_init_uses_default_config_values(self) -> None:
        """Verify __init__ uses default LlamaCppConfig values."""
        with patch("src.models.llm.ChatLlamaCpp") as mock_chat_llamacpp:
            mock_instance = MagicMock()
            mock_chat_llamacpp.return_value = mock_instance

            wrapper = LlamaCppLLMWrapper(LlamaCppConfig())

            mock_chat_llamacpp.assert_called_once_with(
                model_path="./model/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q6_K.gguf",
                temperature=0.1,
                n_ctx=12288,
                n_gpu_layers=-1,
                verbose=False,
                max_tokens=2048,
            )


class TestLlamaCppLLMWrapperInvoke:
    """Tests for LlamaCppLLMWrapper.invoke."""

    def test_invoke_returns_string_response(self) -> None:
        """Verify invoke returns string content from LLM response."""
        config = LlamaCppConfig()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response content"
        mock_model.invoke.return_value = mock_response

        with patch("src.models.llm.ChatLlamaCpp", return_value=mock_model):
            wrapper = LlamaCppLLMWrapper(config)
            result = wrapper.invoke("Test prompt")

        assert result == "Test response content"
        mock_model.invoke.assert_called_once_with("Test prompt")

    def test_invoke_returns_str_when_no_content_attribute(self) -> None:
        """Verify invoke returns str(response) when content attribute is missing."""
        config = LlamaCppConfig()
        mock_model = MagicMock()
        mock_response = MagicMock(spec=[])  # No content attribute
        mock_model.invoke.return_value = mock_response

        with patch("src.models.llm.ChatLlamaCpp", return_value=mock_model):
            wrapper = LlamaCppLLMWrapper(config)
            result = wrapper.invoke("Test prompt")

        assert result == str(mock_response)

    def test_invoke_raises_embedding_error_on_failure(self) -> None:
        """Verify invoke raises EmbeddingError when LLM invocation fails."""
        config = LlamaCppConfig()
        mock_model = MagicMock()
        mock_model.invoke.side_effect = RuntimeError("Connection failed")

        with patch("src.models.llm.ChatLlamaCpp", return_value=mock_model):
            wrapper = LlamaCppLLMWrapper(config)

            with pytest.raises(EmbeddingError) as exc_info:
                wrapper.invoke("Test prompt")

        assert "LLM invocation failed" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, RuntimeError)


class TestLlamaCppLLMWrapperGenerate:
    """Tests for LlamaCppLLMWrapper.generate."""

    def test_generate_returns_list_of_strings(self) -> None:
        """Verify generate returns list of string responses."""
        config = LlamaCppConfig()
        mock_model = MagicMock()
        mock_responses = [
            MagicMock(content="Response 1"),
            MagicMock(content="Response 2"),
            MagicMock(content="Response 3"),
        ]
        mock_model.batch.return_value = mock_responses

        with patch("src.models.llm.ChatLlamaCpp", return_value=mock_model):
            wrapper = LlamaCppLLMWrapper(config)
            result = wrapper.generate(["prompt1", "prompt2", "prompt3"])

        assert result == ["Response 1", "Response 2", "Response 3"]
        mock_model.batch.assert_called_once_with(["prompt1", "prompt2", "prompt3"])

    def test_generate_returns_str_when_no_content_attribute(self) -> None:
        """Verify generate returns str(response) when content attribute is missing."""
        config = LlamaCppConfig()
        mock_model = MagicMock()
        mock_response = MagicMock(spec=[])  # No content attribute
        mock_model.batch.return_value = [mock_response]

        with patch("src.models.llm.ChatLlamaCpp", return_value=mock_model):
            wrapper = LlamaCppLLMWrapper(config)
            result = wrapper.generate(["prompt1"])

        assert result == [str(mock_response)]

    def test_generate_raises_embedding_error_on_failure(self) -> None:
        """Verify generate raises EmbeddingError when batch invocation fails."""
        config = LlamaCppConfig()
        mock_model = MagicMock()
        mock_model.batch.side_effect = RuntimeError("Batch failed")

        with patch("src.models.llm.ChatLlamaCpp", return_value=mock_model):
            wrapper = LlamaCppLLMWrapper(config)

            with pytest.raises(EmbeddingError) as exc_info:
                wrapper.generate(["prompt1", "prompt2"])

        assert "Batch LLM invocation failed" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, RuntimeError)


class TestCreateLLM:
    """Tests for create_llm factory function."""

    def test_create_llm_with_config(self) -> None:
        """Verify create_llm returns wrapper with provided config."""
        config = LlamaCppConfig(
            model_path="./custom/model.gguf",
            temperature=0.5,
            n_ctx=4096,
            n_gpu_layers=10,
            timeout=60,
        )

        with patch("src.models.llm.ChatLlamaCpp"):
            result = create_llm(config)

        assert isinstance(result, LlamaCppLLMWrapper)
        assert result.config == config

    def test_create_llm_without_config_uses_defaults(self) -> None:
        """Verify create_llm uses default config when none provided."""
        with patch("src.models.llm.ChatLlamaCpp"):
            result = create_llm()

        assert isinstance(result, LlamaCppLLMWrapper)
        assert isinstance(result.config, LlamaCppConfig)
        assert result.config.model_path == "./model/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q6_K.gguf"
        assert result.config.embedding_model_path == "./model/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"

    def test_create_llm_returns_llamacppllmwrapper_instance(self) -> None:
        """Verify create_llm returns LlamaCppLLMWrapper instance."""
        with patch("src.models.llm.ChatLlamaCpp"):
            result = create_llm()

        assert isinstance(result, LlamaCppLLMWrapper)