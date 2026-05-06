"""Unit tests for the text chunking module."""

from typing import NamedTuple
from unittest.mock import MagicMock

import pytest

from src.indexing.chunker import Chunk, TextChunker
from src.indexing.parser import Document


class TestTextChunkerInit:
    """Tests for TextChunker.__init__."""

    def test_init_default_values(self) -> None:
        """Test initialization with default values."""
        chunker = TextChunker()
        assert chunker.chunk_size == 500
        assert chunker.chunk_overlap == 50

    def test_init_custom_values(self) -> None:
        """Test initialization with custom values."""
        chunker = TextChunker(chunk_size=1000, chunk_overlap=100)
        assert chunker.chunk_size == 1000
        assert chunker.chunk_overlap == 100


class TestChunkNamedTuple:
    """Tests for the Chunk NamedTuple."""

    def test_chunk_fields(self) -> None:
        """Test Chunk has all required fields."""
        chunk = Chunk(
            content="test content",
            source="test_source",
            chunk_index=0,
            total_chunks=1,
            metadata={"key": "value"},
        )
        assert chunk.content == "test content"
        assert chunk.source == "test_source"
        assert chunk.chunk_index == 0
        assert chunk.total_chunks == 1
        assert chunk.metadata == {"key": "value"}

    def test_chunk_default_metadata(self) -> None:
        """Test Chunk metadata defaults to None."""
        chunk = Chunk(
            content="test content",
            source="test_source",
            chunk_index=0,
            total_chunks=1,
        )
        assert chunk.metadata is None


class TestChunkText:
    """Tests for TextChunker.chunk_text."""

    def test_split_text_correctly(self) -> None:
        """Test basic text splitting."""
        chunker = TextChunker(chunk_size=10, chunk_overlap=0)
        text = "0123456789ABCDEFGHIJ"
        chunks = chunker.chunk_text(text, "test_source")

        assert len(chunks) == 2
        assert chunks[0].content == "0123456789"
        assert chunks[1].content == "ABCDEFGHIJ"

    def test_split_text_with_overlap(self) -> None:
        """Test text splitting with overlap."""
        chunker = TextChunker(chunk_size=10, chunk_overlap=3)
        text = "0123456789ABCDEFGHI"
        chunks = chunker.chunk_text(text, "test_source")

        assert len(chunks) == 3
        assert chunks[0].content == "0123456789"
        assert chunks[1].content == "789ABCDEFG"
        assert chunks[2].content == "EFGHI"

    def test_respects_chunk_size(self) -> None:
        """Test chunks respect chunk_size."""
        chunker = TextChunker(chunk_size=5, chunk_overlap=0)
        text = "0123456789"
        chunks = chunker.chunk_text(text, "test_source")

        for chunk in chunks:
            assert len(chunk.content) <= 5

    def test_respects_chunk_overlap(self) -> None:
        """Test chunks respect chunk_overlap."""
        chunker = TextChunker(chunk_size=10, chunk_overlap=5)
        text = "AAAAABBBBBCCCCC"
        chunks = chunker.chunk_text(text, "test_source")

        assert len(chunks) == 3
        assert chunks[0].content == "AAAAABBBBB"
        assert chunks[1].content == "BBBBBCCCCC"
        assert chunks[1].content.startswith("BBBBB")
        assert chunks[0].content.endswith("BBBBB")

    def test_handles_empty_text(self) -> None:
        """Test empty text returns empty list."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("", "test_source")
        assert chunks == []

    def test_handles_single_char_text(self) -> None:
        """Test single character text returns single chunk."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("A", "test_source")
        assert len(chunks) == 1
        assert chunks[0].content == "A"

    def test_sets_total_chunks_correctly(self) -> None:
        """Test total_chunks is set correctly."""
        chunker = TextChunker(chunk_size=10, chunk_overlap=0)
        text = "0123456789ABCDEFGHI"
        chunks = chunker.chunk_text(text, "test_source")

        assert len(chunks) == 2
        assert chunks[0].total_chunks == 2
        assert chunks[1].total_chunks == 2

    def test_sets_chunk_index_correctly(self) -> None:
        """Test chunk_index is set correctly."""
        chunker = TextChunker(chunk_size=10, chunk_overlap=0)
        text = "0123456789ABCDEFGHI"
        chunks = chunker.chunk_text(text, "test_source")

        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1

    def test_chunk_index_sequential(self) -> None:
        """Test chunk indices are sequential."""
        chunker = TextChunker(chunk_size=5, chunk_overlap=0)
        text = "ABCDEFGHIJ"
        chunks = chunker.chunk_text(text, "test_source")

        assert len(chunks) == 2
        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1

    def test_metadata_passed_to_chunks(self) -> None:
        """Test metadata is passed through to all chunks."""
        chunker = TextChunker(chunk_size=10, chunk_overlap=0)
        text = "0123456789ABCDEFGHI"
        metadata = {"page": "1", "section": "intro"}
        chunks = chunker.chunk_text(text, "test_source", metadata=metadata)

        assert len(chunks) == 2
        for chunk in chunks:
            assert chunk.metadata == metadata

    def test_no_metadata(self) -> None:
        """Test chunks have None metadata when none provided."""
        chunker = TextChunker(chunk_size=10, chunk_overlap=0)
        text = "0123456789"
        chunks = chunker.chunk_text(text, "test_source")

        assert len(chunks) == 1
        assert chunks[0].metadata is None

    def test_source_set_correctly(self) -> None:
        """Test source is set correctly on chunks."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("test content", "my_source")

        assert len(chunks) == 1
        assert chunks[0].source == "my_source"

    def test_text_shorter_than_chunk_size(self) -> None:
        """Test text shorter than chunk_size returns single chunk."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=10)
        text = "short"
        chunks = chunker.chunk_text(text, "test_source")

        assert len(chunks) == 1
        assert chunks[0].content == "short"
        assert chunks[0].total_chunks == 1
        assert chunks[0].chunk_index == 0

    def test_exact_multiple_of_chunk_size(self) -> None:
        """Test text that is exact multiple of chunk_size."""
        chunker = TextChunker(chunk_size=5, chunk_overlap=0)
        text = "ABCDEFGHIJ"
        chunks = chunker.chunk_text(text, "test_source")

        assert len(chunks) == 2
        assert chunks[0].content == "ABCDE"
        assert chunks[1].content == "FGHIJ"

    def test_last_chunk_shorter(self) -> None:
        """Test last chunk may be shorter."""
        chunker = TextChunker(chunk_size=10, chunk_overlap=0)
        text = "0123456789ABC"
        chunks = chunker.chunk_text(text, "test_source")

        assert len(chunks) == 2
        assert chunks[0].content == "0123456789"
        assert chunks[1].content == "ABC"


class TestChunkDocuments:
    """Tests for TextChunker.chunk_documents."""

    def test_chunks_multiple_documents(self) -> None:
        """Test chunking multiple documents."""
        chunker = TextChunker(chunk_size=5, chunk_overlap=0)
        doc1 = Document(content="1234567890", source="doc1", metadata=None)
        doc2 = Document(content="ABCDEFGHIJ", source="doc2", metadata=None)
        documents = [doc1, doc2]

        chunks = chunker.chunk_documents(documents)

        assert len(chunks) == 4
        assert chunks[0].source == "doc1"
        assert chunks[1].source == "doc1"
        assert chunks[2].source == "doc2"
        assert chunks[3].source == "doc2"

    def test_chunks_empty_document_list(self) -> None:
        """Test chunking empty document list."""
        chunker = TextChunker()
        chunks = chunker.chunk_documents([])
        assert chunks == []

    def test_single_document_list(self) -> None:
        """Test chunking single document in list."""
        chunker = TextChunker(chunk_size=5, chunk_overlap=0)
        doc = Document(content="ABCDEFGH", source="single_doc", metadata=None)
        chunks = chunker.chunk_documents([doc])

        assert len(chunks) == 2
        assert all(c.source == "single_doc" for c in chunks)

    def test_documents_metadata_preserved(self) -> None:
        """Test metadata from each document is preserved."""
        chunker = TextChunker(chunk_size=5, chunk_overlap=0)
        doc1 = Document(content="1234567890", source="doc1", metadata={"type": "text"})
        doc2 = Document(content="ABCDEFGHIJ", source="doc2", metadata={"type": "code"})
        documents = [doc1, doc2]

        chunks = chunker.chunk_documents(documents)

        assert len(chunks) == 4
        assert chunks[0].metadata == {"type": "text"}
        assert chunks[2].metadata == {"type": "code"}

    def test_multiple_documents_chunk_indices(self) -> None:
        """Test chunk indices reset per document."""
        chunker = TextChunker(chunk_size=5, chunk_overlap=0)
        doc1 = Document(content="ABCDE", source="doc1", metadata=None)
        doc2 = Document(content="FGHIJ", source="doc2", metadata=None)
        documents = [doc1, doc2]

        chunks = chunker.chunk_documents(documents)

        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 0