"""Unit tests for src/exceptions.py following TDD methodology."""

import pytest

from src.exceptions import (
    RAGError,
    DocumentParseError,
    ChunkingError,
    EmbeddingError,
    IndexError,
    RetrievalError,
    ConfigurationError,
    PipelineError,
)


class TestRAGError:
    """Tests for base RAGError exception."""

    def test_can_be_instantiated_with_message(self):
        """RAGError can be instantiated with a message."""
        error = RAGError("Something went wrong")
        assert error.message == "Something went wrong"
        assert str(error) == "Something went wrong"

    def test_inherits_from_exception(self):
        """RAGError inherits from Exception."""
        error = RAGError("test")
        assert isinstance(error, Exception)


class TestDocumentParseError:
    """Tests for DocumentParseError exception."""

    def test_can_be_instantiated_with_message_only(self):
        """DocumentParseError can be instantiated with just a message."""
        error = DocumentParseError("Failed to parse PDF")
        assert error.message == "Failed to parse PDF"
        assert error.source is None

    def test_can_be_instantiated_with_message_and_source(self):
        """DocumentParseError can be instantiated with message and source."""
        error = DocumentParseError("Failed to parse PDF", source="/path/to/doc.pdf")
        assert error.message == "Failed to parse PDF"
        assert error.source == "/path/to/doc.pdf"

    def test_inherits_from_rag_error(self):
        """DocumentParseError inherits from RAGError."""
        error = DocumentParseError("test")
        assert isinstance(error, RAGError)


class TestChunkingError:
    """Tests for ChunkingError exception."""

    def test_can_be_instantiated_with_message(self):
        """ChunkingError can be instantiated with a message."""
        error = ChunkingError("Chunk size too large")
        assert error.message == "Chunk size too large"

    def test_inherits_from_rag_error(self):
        """ChunkingError inherits from RAGError."""
        error = ChunkingError("test")
        assert isinstance(error, RAGError)


class TestEmbeddingError:
    """Tests for EmbeddingError exception."""

    def test_can_be_instantiated_with_message(self):
        """EmbeddingError can be instantiated with a message."""
        error = EmbeddingError("Model not loaded")
        assert error.message == "Model not loaded"

    def test_inherits_from_rag_error(self):
        """EmbeddingError inherits from RAGError."""
        error = EmbeddingError("test")
        assert isinstance(error, RAGError)


class TestIndexError:
    """Tests for IndexError exception."""

    def test_can_be_instantiated_with_message(self):
        """IndexError can be instantiated with a message."""
        error = IndexError("Index not found")
        assert error.message == "Index not found"

    def test_inherits_from_rag_error(self):
        """IndexError inherits from RAGError."""
        error = IndexError("test")
        assert isinstance(error, RAGError)


class TestRetrievalError:
    """Tests for RetrievalError exception."""

    def test_can_be_instantiated_with_message(self):
        """RetrievalError can be instantiated with a message."""
        error = RetrievalError("No results returned")
        assert error.message == "No results returned"

    def test_inherits_from_rag_error(self):
        """RetrievalError inherits from RAGError."""
        error = RetrievalError("test")
        assert isinstance(error, RAGError)


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_can_be_instantiated_with_message(self):
        """ConfigurationError can be instantiated with a message."""
        error = ConfigurationError("Invalid API key")
        assert error.message == "Invalid API key"

    def test_inherits_from_rag_error(self):
        """ConfigurationError inherits from RAGError."""
        error = ConfigurationError("test")
        assert isinstance(error, RAGError)


class TestPipelineError:
    """Tests for PipelineError exception."""

    def test_can_be_instantiated_with_message(self):
        """PipelineError can be instantiated with a message."""
        error = PipelineError("Pipeline execution failed")
        assert error.message == "Pipeline execution failed"

    def test_inherits_from_rag_error(self):
        """PipelineError inherits from RAGError."""
        error = PipelineError("test")
        assert isinstance(error, RAGError)


class TestExceptionHierarchy:
    """Tests for exception hierarchy catching behavior."""

    @pytest.mark.parametrize(
        "exception_class,message",
        [
            (DocumentParseError, "parse error"),
            (ChunkingError, "chunking error"),
            (EmbeddingError, "embedding error"),
            (IndexError, "index error"),
            (RetrievalError, "retrieval error"),
            (ConfigurationError, "config error"),
            (PipelineError, "pipeline error"),
        ],
    )
    def test_all_subclasses_catchable_as_rag_error(self, exception_class, message):
        """All RAGError subclasses can be caught as RAGError."""
        with pytest.raises(RAGError):
            raise exception_class(message)

    def test_rag_error_catchable_as_exception(self):
        """RAGError itself is catchable as Exception."""
        with pytest.raises(Exception):
            raise RAGError("base error")

    def test_document_parse_error_catchable_as_rag_error(self):
        """DocumentParseError can be caught as RAGError."""
        with pytest.raises(RAGError):
            raise DocumentParseError("parse failed", source="/test.pdf")