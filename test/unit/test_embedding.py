"""Unit tests for src/models/embedding.py"""

from unittest.mock import MagicMock, patch

import pytest

from src.config import LlamaCppConfig
from src.exceptions import EmbeddingError
from src.models.embedding import LlamaCppEmbeddingWrapper, create_embedding


class TestLlamaCppEmbeddingWrapperInit:
    """Tests for LlamaCppEmbeddingWrapper.__init__."""

    def test_init_creates_llama_with_correct_config(self) -> None:
        """Verify __init__ creates Llama with correct configuration."""
        config = LlamaCppConfig(
            embedding_model_path="./model/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf",
            n_gpu_layers=-1,
            timeout=120,
        )

        with patch("src.models.embedding.Llama") as mock_llama:
            mock_instance = MagicMock()
            mock_llama.return_value = mock_instance

            wrapper = LlamaCppEmbeddingWrapper(config)

            mock_llama.assert_called_once_with(
                model_path="./model/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf",
                embedding=True,
                n_gpu_layers=-1,
                verbose=False,
            )
            assert wrapper.config == config
            assert wrapper._model is mock_instance

    def test_init_uses_default_config_values(self) -> None:
        """Verify __init__ uses default LlamaCppConfig values."""
        with patch("src.models.embedding.Llama") as mock_llama:
            mock_instance = MagicMock()
            mock_llama.return_value = mock_instance

            wrapper = LlamaCppEmbeddingWrapper(LlamaCppConfig())

            mock_llama.assert_called_once_with(
                model_path="./model/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf",
                embedding=True,
                n_gpu_layers=-1,
                verbose=False,
            )


class TestLlamaCppEmbeddingWrapperEmbed:
    """Tests for LlamaCppEmbeddingWrapper.embed."""

    def test_embed_returns_list_of_floats(self) -> None:
        """Verify embed returns list of floats."""
        config = LlamaCppConfig()
        mock_model = MagicMock()
        mock_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_model.embed.return_value = mock_embedding

        with patch("src.models.embedding.Llama", return_value=mock_model):
            wrapper = LlamaCppEmbeddingWrapper(config)
            result = wrapper.embed("test text")

        assert isinstance(result, list)
        assert result == mock_embedding
        assert all(isinstance(x, float) for x in result)
        mock_model.embed.assert_called_once_with("test text")

    def test_embed_returns_empty_list_for_empty_text(self) -> None:
        """Verify embed returns empty list for empty text input."""
        config = LlamaCppConfig()
        mock_model = MagicMock()
        mock_model.embed.return_value = []

        with patch("src.models.embedding.Llama", return_value=mock_model):
            wrapper = LlamaCppEmbeddingWrapper(config)
            result = wrapper.embed("")

        assert result == []
        mock_model.embed.assert_called_once_with("")

    def test_embed_raises_embedding_error_on_failure(self) -> None:
        """Verify embed raises EmbeddingError when embedding generation fails."""
        config = LlamaCppConfig()
        mock_model = MagicMock()
        mock_model.embed.side_effect = RuntimeError("Connection refused")

        with patch("src.models.embedding.Llama", return_value=mock_model):
            wrapper = LlamaCppEmbeddingWrapper(config)

            with pytest.raises(EmbeddingError) as exc_info:
                wrapper.embed("test text")

        assert "Embedding generation failed" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, RuntimeError)


class TestLlamaCppEmbeddingWrapperEmbedBatch:
    """Tests for LlamaCppEmbeddingWrapper.embed_batch."""

    def test_embed_batch_returns_list_of_list_of_floats(self) -> None:
        """Verify embed_batch returns list of list of floats."""
        config = LlamaCppConfig()
        mock_model = MagicMock()
        mock_embeddings = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9],
        ]
        mock_model.embed.side_effect = mock_embeddings

        with patch("src.models.embedding.Llama", return_value=mock_model):
            wrapper = LlamaCppEmbeddingWrapper(config)
            result = wrapper.embed_batch(["text1", "text2", "text3"])

        assert isinstance(result, list)
        assert len(result) == 3
        assert result == mock_embeddings
        assert all(isinstance(x, list) for x in result)
        assert mock_model.embed.call_count == 3

    def test_embed_batch_returns_empty_list_for_empty_input(self) -> None:
        """Verify embed_batch returns empty list for empty input."""
        config = LlamaCppConfig()
        mock_model = MagicMock()
        mock_model.embed.return_value = []

        with patch("src.models.embedding.Llama", return_value=mock_model):
            wrapper = LlamaCppEmbeddingWrapper(config)
            result = wrapper.embed_batch([])

        assert result == []

    def test_embed_batch_raises_embedding_error_on_failure(self) -> None:
        """Verify embed_batch raises EmbeddingError when batch embedding fails."""
        config = LlamaCppConfig()
        mock_model = MagicMock()
        mock_model.embed.side_effect = RuntimeError("Timeout")

        with patch("src.models.embedding.Llama", return_value=mock_model):
            wrapper = LlamaCppEmbeddingWrapper(config)

            with pytest.raises(EmbeddingError) as exc_info:
                wrapper.embed_batch(["text1", "text2"])

        assert "Batch embedding generation failed" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, RuntimeError)

    def test_embed_batch_preserves_order_of_results(self) -> None:
        """Verify embed_batch returns results in same order as input."""
        config = LlamaCppConfig()
        mock_model = MagicMock()
        mock_embeddings = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        mock_model.embed.side_effect = mock_embeddings

        with patch("src.models.embedding.Llama", return_value=mock_model):
            wrapper = LlamaCppEmbeddingWrapper(config)
            result = wrapper.embed_batch(["first", "second", "third"])

        assert result[0] == [1.0, 2.0]
        assert result[1] == [3.0, 4.0]
        assert result[2] == [5.0, 6.0]


class TestCreateEmbedding:
    """Tests for create_embedding factory function."""

    def test_create_embedding_with_config(self) -> None:
        """Verify create_embedding returns wrapper with provided config."""
        config = LlamaCppConfig(
            embedding_model_path="./custom/embedding.gguf",
            n_gpu_layers=10,
            timeout=60,
        )

        with patch("src.models.embedding.Llama"):
            result = create_embedding(config)

        assert isinstance(result, LlamaCppEmbeddingWrapper)
        assert result.config == config

    def test_create_embedding_without_config_uses_defaults(self) -> None:
        """Verify create_embedding uses default config when none provided."""
        with patch("src.models.embedding.Llama"):
            result = create_embedding()

        assert isinstance(result, LlamaCppEmbeddingWrapper)
        assert isinstance(result.config, LlamaCppConfig)
        assert result.config.model_path == "./model/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q6_K.gguf"
        assert result.config.embedding_model_path == "./model/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"

    def test_create_embedding_returns_llamacppembeddingwrapper_instance(self) -> None:
        """Verify create_embedding returns LlamaCppEmbeddingWrapper instance."""
        with patch("src.models.embedding.Llama"):
            result = create_embedding()

        assert isinstance(result, LlamaCppEmbeddingWrapper)