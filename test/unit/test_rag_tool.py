"""Unit tests for RAG tool."""

from unittest.mock import MagicMock, patch

import pytest

from src.tools.rag_tool import rag_retrieve, set_retriever


class TestSetRetriever:
    """Tests for set_retriever function."""

    def test_set_retriever_stores_global_retriever(self) -> None:
        """Should store the retriever in global _retriever variable."""
        mock_retriever = MagicMock()

        set_retriever(mock_retriever)

        from src.tools.rag_tool import _retriever
        assert _retriever is mock_retriever

    def test_set_retriever_replaces_existing_retriever(self) -> None:
        """Should replace existing retriever with new one."""
        mock_retriever1 = MagicMock()
        mock_retriever2 = MagicMock()

        set_retriever(mock_retriever1)
        set_retriever(mock_retriever2)

        from src.tools.rag_tool import _retriever
        assert _retriever is mock_retriever2


class TestRagRetrieve:
    """Tests for rag_retrieve tool function."""

    def setup_method(self) -> None:
        """Reset global _retriever before each test."""
        from src.tools.rag_tool import _retriever
        _retriever = None

    def test_rag_retrieve_returns_error_when_retriever_not_initialized(self) -> None:
        """Should return error message when _retriever is None."""
        from src.tools import rag_tool
        rag_tool._retriever = None

        result = rag_retrieve.invoke("test query")

        assert result == "Error: RAG retriever not initialized."

    def test_rag_retrieve_invokes_retriever_with_query(self) -> None:
        """Should call retriever.invoke with the query string."""
        mock_retriever = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "Test content"
        mock_doc.metadata = {"source": "test.md"}
        mock_retriever.invoke.return_value = [mock_doc]

        set_retriever(mock_retriever)
        rag_retrieve.invoke("test query")

        mock_retriever.invoke.assert_called_once_with("test query")

    def test_rag_retrieve_returns_no_results_message_when_docs_empty(self) -> None:
        """Should return 'No relevant information found.' when docs list is empty."""
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []

        set_retriever(mock_retriever)
        result = rag_retrieve.invoke("test query")

        assert result == "No relevant information found."

    def test_rag_retrieve_formats_single_document(self) -> None:
        """Should format single document with chunk number and source."""
        mock_retriever = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "Document content here"
        mock_doc.metadata = {"source": "document.md"}
        mock_retriever.invoke.return_value = [mock_doc]

        set_retriever(mock_retriever)
        result = rag_retrieve.invoke("test query")

        assert "[Chunk 1]" in result
        assert "Source: document.md" in result
        assert "Document content here" in result

    def test_rag_retrieve_formats_multiple_documents(self) -> None:
        """Should format multiple documents with chunk numbers and sources."""
        mock_retriever = MagicMock()
        mock_doc1 = MagicMock()
        mock_doc1.page_content = "First document"
        mock_doc1.metadata = {"source": "doc1.md"}

        mock_doc2 = MagicMock()
        mock_doc2.page_content = "Second document"
        mock_doc2.metadata = {"source": "doc2.md"}

        mock_retriever.invoke.return_value = [mock_doc1, mock_doc2]

        set_retriever(mock_retriever)
        result = rag_retrieve.invoke("test query")

        assert "[Chunk 1]" in result
        assert "[Chunk 2]" in result
        assert "First document" in result
        assert "Second document" in result
        assert "Source: doc1.md" in result
        assert "Source: doc2.md" in result

    def test_rag_retrieve_handles_missing_source_in_metadata(self) -> None:
        """Should use 'Unknown' source when metadata has no source key."""
        mock_retriever = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "Content"
        mock_doc.metadata = {}
        mock_retriever.invoke.return_value = [mock_doc]

        set_retriever(mock_retriever)
        result = rag_retrieve.invoke("test query")

        assert "Source: Unknown" in result

    def test_rag_retrieve_separates_chunks_with_dashes(self) -> None:
        """Should separate formatted chunks with '---\n\n'."""
        mock_retriever = MagicMock()
        mock_doc1 = MagicMock()
        mock_doc1.page_content = "First"
        mock_doc1.metadata = {"source": "doc1.md"}

        mock_doc2 = MagicMock()
        mock_doc2.page_content = "Second"
        mock_doc2.metadata = {"source": "doc2.md"}

        mock_retriever.invoke.return_value = [mock_doc1, mock_doc2]

        set_retriever(mock_retriever)
        result = rag_retrieve.invoke("test query")

        assert "---\n\n" in result

    def test_rag_retrieve_returns_string(self) -> None:
        """Should return a string result."""
        mock_retriever = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "Content"
        mock_doc.metadata = {"source": "doc.md"}
        mock_retriever.invoke.return_value = [mock_doc]

        set_retriever(mock_retriever)
        result = rag_retrieve.invoke("test query")

        assert isinstance(result, str)
