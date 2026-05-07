"""Unit tests for embedding service."""

from unittest.mock import MagicMock, patch

import pytest

from src.pipeline.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Tests for EmbeddingService class."""

    def test_initialization_sets_model_path(self) -> None:
        """Should store model_path on initialization."""
        service = EmbeddingService(model_path="/path/to/model.gguf")

        assert service._model_path == "/path/to/model.gguf"

    def test_initialization_sets_default_n_ctx(self) -> None:
        """Should set default n_ctx to 512."""
        service = EmbeddingService(model_path="/path/to/model.gguf")

        assert service._n_ctx == 512

    def test_initialization_sets_default_n_threads(self) -> None:
        """Should set default n_threads to 4."""
        service = EmbeddingService(model_path="/path/to/model.gguf")

        assert service._n_threads == 4

    def test_initialization_accepts_custom_n_ctx(self) -> None:
        """Should accept custom n_ctx value."""
        service = EmbeddingService(
            model_path="/path/to/model.gguf",
            n_ctx=1024
        )

        assert service._n_ctx == 1024

    def test_initialization_accepts_custom_n_threads(self) -> None:
        """Should accept custom n_threads value."""
        service = EmbeddingService(
            model_path="/path/to/model.gguf",
            n_threads=8
        )

        assert service._n_threads == 8

    def test_initialization_sets_embeddings_to_none(self) -> None:
        """Should initialize _embeddings as None (lazy initialization)."""
        service = EmbeddingService(model_path="/path/to/model.gguf")

        assert service._embeddings is None

    @patch("src.pipeline.embedding_service.LlamaCppEmbeddings")
    def test_get_embeddings_creates_llamacpp_instance(
        self, mock_llamacpp_class: MagicMock
    ) -> None:
        """Should create LlamaCppEmbeddings instance on first call."""
        service = EmbeddingService(model_path="/path/to/model.gguf")
        service.get_embeddings()

        mock_llamacpp_class.assert_called_once_with(
            model_path="/path/to/model.gguf",
            n_ctx=512,
            n_threads=4,
        )

    @patch("src.pipeline.embedding_service.LlamaCppEmbeddings")
    def test_get_embeddings_returns_llamacpp_instance(
        self, mock_llamacpp_class: MagicMock
    ) -> None:
        """Should return LlamaCppEmbeddings instance."""
        mock_embeddings = MagicMock()
        mock_llamacpp_class.return_value = mock_embeddings

        service = EmbeddingService(model_path="/path/to/model.gguf")
        result = service.get_embeddings()

        assert result is mock_embeddings

    @patch("src.pipeline.embedding_service.LlamaCppEmbeddings")
    def test_get_embeddings_uses_custom_n_ctx_and_n_threads(
        self, mock_llamacpp_class: MagicMock
    ) -> None:
        """Should pass custom n_ctx and n_threads to LlamaCppEmbeddings."""
        service = EmbeddingService(
            model_path="/path/to/model.gguf",
            n_ctx=1024,
            n_threads=8,
        )
        service.get_embeddings()

        mock_llamacpp_class.assert_called_once_with(
            model_path="/path/to/model.gguf",
            n_ctx=1024,
            n_threads=8,
        )

    @patch("src.pipeline.embedding_service.LlamaCppEmbeddings")
    def test_get_embeddings_caches_instance(self, mock_llamacpp_class: MagicMock) -> None:
        """Should cache and reuse LlamaCppEmbeddings instance on subsequent calls."""
        mock_embeddings = MagicMock()
        mock_llamacpp_class.return_value = mock_embeddings

        service = EmbeddingService(model_path="/path/to/model.gguf")

        first_call = service.get_embeddings()
        second_call = service.get_embeddings()

        assert first_call is second_call
        assert mock_llamacpp_class.call_count == 1

    @patch("src.pipeline.embedding_service.LlamaCppEmbeddings")
    def test_get_embeddings_stores_instance_in_cache(
        self, mock_llamacpp_class: MagicMock
    ) -> None:
        """Should store created instance in _embeddings."""
        mock_embeddings = MagicMock()
        mock_llamacpp_class.return_value = mock_embeddings

        service = EmbeddingService(model_path="/path/to/model.gguf")
        service.get_embeddings()

        assert service._embeddings is mock_embeddings

    @patch("src.pipeline.embedding_service.LlamaCppEmbeddings")
    def test_get_embeddings_lazy_initialization(self, mock_llamacpp_class: MagicMock) -> None:
        """Should not create LlamaCppEmbeddings until get_embeddings is called."""
        service = EmbeddingService(model_path="/path/to/model.gguf")

        mock_llamacpp_class.assert_not_called()

        service.get_embeddings()

        mock_llamacpp_class.assert_called_once()
