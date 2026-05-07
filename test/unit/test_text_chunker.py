"""Unit tests for text chunker."""

from unittest.mock import MagicMock, patch

import pytest

from src.pipeline.text_chunker import chunk_documents


class TestChunkDocuments:
    """Tests for chunk_documents function."""

    def test_chunk_documents_returns_empty_list_for_empty_input(self) -> None:
        """Should return empty list when given empty text list."""
        result = chunk_documents([])
        assert result == []

    @patch("src.pipeline.text_chunker.RecursiveCharacterTextSplitter")
    def test_chunk_documents_uses_default_chunk_size_and_overlap(
        self, mock_splitter_class: MagicMock
    ) -> None:
        """Should use default chunk_size=500 and chunk_overlap=50."""
        mock_splitter = MagicMock()
        mock_splitter.create_documents.return_value = []
        mock_splitter_class.return_value = mock_splitter

        chunk_documents(["some text"])

        mock_splitter_class.assert_called_once_with(
            chunk_size=500,
            chunk_overlap=50,
        )

    @patch("src.pipeline.text_chunker.RecursiveCharacterTextSplitter")
    def test_chunk_documents_passes_custom_chunk_size_and_overlap(
        self, mock_splitter_class: MagicMock
    ) -> None:
        """Should pass custom chunk_size and chunk_overlap to splitter."""
        mock_splitter = MagicMock()
        mock_splitter.create_documents.return_value = []
        mock_splitter_class.return_value = mock_splitter

        chunk_documents(["some text"], chunk_size=1000, chunk_overlap=100)

        mock_splitter_class.assert_called_once_with(
            chunk_size=1000,
            chunk_overlap=100,
        )

    @patch("src.pipeline.text_chunker.RecursiveCharacterTextSplitter")
    def test_chunk_documents_returns_list_of_dicts_with_content_and_metadata(
        self, mock_splitter_class: MagicMock
    ) -> None:
        """Should return list of dicts with 'content' and 'metadata' keys."""
        mock_chunk1 = MagicMock()
        mock_chunk1.page_content = "First chunk"
        mock_chunk1.metadata = {"source": "doc1"}

        mock_chunk2 = MagicMock()
        mock_chunk2.page_content = "Second chunk"
        mock_chunk2.metadata = {"source": "doc1"}

        mock_splitter = MagicMock()
        mock_splitter.create_documents.return_value = [mock_chunk1, mock_chunk2]
        mock_splitter_class.return_value = mock_splitter

        result = chunk_documents(["long text"])

        assert len(result) == 2
        assert result[0]["content"] == "First chunk"
        assert result[0]["metadata"] == {"source": "doc1"}
        assert result[1]["content"] == "Second chunk"
        assert result[1]["metadata"] == {"source": "doc1"}

    @patch("src.pipeline.text_chunker.RecursiveCharacterTextSplitter")
    def test_chunk_documents_calls_create_documents_with_texts(
        self, mock_splitter_class: MagicMock
    ) -> None:
        """Should call create_documents with the input texts."""
        mock_splitter = MagicMock()
        mock_splitter.create_documents.return_value = []
        mock_splitter_class.return_value = mock_splitter

        input_texts = ["text one", "text two", "text three"]
        chunk_documents(input_texts)

        mock_splitter.create_documents.assert_called_once_with(input_texts)

    @patch("src.pipeline.text_chunker.RecursiveCharacterTextSplitter")
    def test_chunk_documents_handles_single_text(
        self, mock_splitter_class: MagicMock
    ) -> None:
        """Should handle single text input in a list."""
        mock_chunk = MagicMock()
        mock_chunk.page_content = "single chunk"
        mock_chunk.metadata = {}

        mock_splitter = MagicMock()
        mock_splitter.create_documents.return_value = [mock_chunk]
        mock_splitter_class.return_value = mock_splitter

        result = chunk_documents(["only one text"])

        assert len(result) == 1
        assert result[0]["content"] == "single chunk"

    @patch("src.pipeline.text_chunker.RecursiveCharacterTextSplitter")
    def test_chunk_documents_preserves_metadata_from_splitter(
        self, mock_splitter_class: MagicMock
    ) -> None:
        """Should preserve metadata from RecursiveCharacterTextSplitter output."""
        mock_chunk = MagicMock()
        mock_chunk.page_content = "content with metadata"
        mock_chunk.metadata = {"page": 1, "source": "document.md"}

        mock_splitter = MagicMock()
        mock_splitter.create_documents.return_value = [mock_chunk]
        mock_splitter_class.return_value = mock_splitter

        result = chunk_documents(["text"])

        assert result[0]["metadata"] == {"page": 1, "source": "document.md"}
