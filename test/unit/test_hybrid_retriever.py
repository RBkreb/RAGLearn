"""Tests for src.retrieval.hybrid_retriever module."""

from unittest.mock import MagicMock

import pytest

from src.exceptions import RetrievalError
from src.retrieval.hybrid_retriever import HybridRetriever, RetrievalResult


class TestRetrievalResultNamedTuple:
    """Tests for RetrievalResult NamedTuple."""

    def test_retrieval_result_has_four_fields(self) -> None:
        """Test that RetrievalResult has content, source, distance, metadata fields."""
        result = RetrievalResult(
            content="test content",
            source="test_source",
            distance=0.5,
            metadata={"key": "value"},
        )
        assert result.content == "test content"
        assert result.source == "test_source"
        assert result.distance == 0.5
        assert result.metadata == {"key": "value"}

    def test_retrieval_result_metadata_defaults_to_none(self) -> None:
        """Test that metadata defaults to None when not provided."""
        result = RetrievalResult(content="content", source="source", distance=0.1)
        assert result.metadata is None

    def test_retrieval_result_is_immutable(self) -> None:
        """Test that RetrievalResult cannot be modified after creation."""
        result = RetrievalResult(content="content", source="source", distance=0.1)
        with pytest.raises(AttributeError):
            result.content = "new content"


class TestHybridRetrieverInit:
    """Tests for HybridRetriever.__init__."""

    def test_init_stores_embedding_wrapper(self) -> None:
        """Test that __init__ stores the embedding_wrapper."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        retriever = HybridRetriever(mock_embedding, mock_index)
        assert retriever.embedding_wrapper is mock_embedding

    def test_init_stores_index_manager(self) -> None:
        """Test that __init__ stores the index_manager."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        retriever = HybridRetriever(mock_embedding, mock_index)
        assert retriever.index_manager is mock_index

    def test_init_stores_top_k(self) -> None:
        """Test that __init__ stores the top_k parameter."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        retriever = HybridRetriever(mock_embedding, mock_index, top_k=10)
        assert retriever.top_k == 10

    def test_init_default_top_k_is_four(self) -> None:
        """Test that default top_k is 4."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        retriever = HybridRetriever(mock_embedding, mock_index)
        assert retriever.top_k == 4


class TestHybridRetrieverRetrieve:
    """Tests for HybridRetriever.retrieve."""

    def test_retrieve_calls_embedding_embed(self) -> None:
        """Test that retrieve calls embedding_wrapper.embed with query."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        mock_embedding.embed.return_value = [0.1, 0.2, 0.3]
        mock_index.similarity_search.return_value = []

        retriever = HybridRetriever(mock_embedding, mock_index)
        retriever.retrieve("test query")

        mock_embedding.embed.assert_called_once_with("test query")

    def test_retrieve_calls_similarity_search(self) -> None:
        """Test that retrieve calls index_manager.similarity_search."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        mock_embedding.embed.return_value = [0.1, 0.2, 0.3]
        mock_index.similarity_search.return_value = []

        retriever = HybridRetriever(mock_embedding, mock_index, top_k=5)
        retriever.retrieve("test query")

        mock_index.similarity_search.assert_called_once_with(
            [0.1, 0.2, 0.3], top_k=5
        )

    def test_retrieve_returns_list_of_retrieval_result(self) -> None:
        """Test that retrieve returns list of RetrievalResult."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        mock_embedding.embed.return_value = [0.1, 0.2, 0.3]
        mock_index.similarity_search.return_value = [
            {
                "id": "doc1_chunk0",
                "document": "First document content",
                "distance": 0.1,
                "metadata": {"page": 1},
            },
            {
                "id": "doc2_chunk1",
                "document": "Second document content",
                "distance": 0.2,
                "metadata": {"page": 2},
            },
        ]

        retriever = HybridRetriever(mock_embedding, mock_index)
        results = retriever.retrieve("test query")

        assert len(results) == 2
        assert all(isinstance(r, RetrievalResult) for r in results)
        assert results[0].content == "First document content"
        assert results[0].source == "doc1"
        assert results[0].distance == 0.1
        assert results[0].metadata == {"page": 1}
        assert results[1].content == "Second document content"
        assert results[1].source == "doc2"
        assert results[1].distance == 0.2

    def test_retrieve_extracts_source_from_id_with_underscore(self) -> None:
        """Test that source is extracted from id before underscore."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        mock_embedding.embed.return_value = [0.1]
        mock_index.similarity_search.return_value = [
            {"id": "myfile_chunk0", "document": "content", "distance": 0.1, "metadata": None},
        ]

        retriever = HybridRetriever(mock_embedding, mock_index)
        results = retriever.retrieve("query")

        assert results[0].source == "myfile"

    def test_retrieve_uses_id_as_source_when_no_underscore(self) -> None:
        """Test that id is used as source when no underscore present."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        mock_embedding.embed.return_value = [0.1]
        mock_index.similarity_search.return_value = [
            {"id": "singleid", "document": "content", "distance": 0.1, "metadata": None},
        ]

        retriever = HybridRetriever(mock_embedding, mock_index)
        results = retriever.retrieve("query")

        assert results[0].source == "singleid"

    def test_retrieve_raises_retrieval_error_on_embed_failure(self) -> None:
        """Test that RetrievalError is raised when embed fails."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        mock_embedding.embed.side_effect = Exception("Embedding failed")

        retriever = HybridRetriever(mock_embedding, mock_index)

        with pytest.raises(RetrievalError, match="Retrieval failed"):
            retriever.retrieve("test query")

    def test_retrieve_raises_retrieval_error_on_similarity_search_failure(self) -> None:
        """Test that RetrievalError is raised when similarity_search fails."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        mock_embedding.embed.return_value = [0.1]
        mock_index.similarity_search.side_effect = Exception("Search failed")

        retriever = HybridRetriever(mock_embedding, mock_index)

        with pytest.raises(RetrievalError, match="Retrieval failed"):
            retriever.retrieve("test query")


class TestHybridRetrieverRetrieveWithScores:
    """Tests for HybridRetriever.retrieve_with_scores."""

    def test_retrieve_with_scores_returns_all_results_when_below_threshold(
        self,
    ) -> None:
        """Test that all results are returned when all distances are below threshold."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        mock_embedding.embed.return_value = [0.1]
        mock_index.similarity_search.return_value = [
            {"id": "doc1", "document": "content1", "distance": 0.3, "metadata": None},
            {"id": "doc2", "document": "content2", "distance": 0.4, "metadata": None},
        ]

        retriever = HybridRetriever(mock_embedding, mock_index)
        results = retriever.retrieve_with_scores("query", threshold=0.5)

        assert len(results) == 2

    def test_retrieve_with_scores_filters_by_threshold(self) -> None:
        """Test that results with distance above threshold are filtered out."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        mock_embedding.embed.return_value = [0.1]
        mock_index.similarity_search.return_value = [
            {"id": "doc1", "document": "content1", "distance": 0.3, "metadata": None},
            {"id": "doc2", "document": "content2", "distance": 0.7, "metadata": None},
            {"id": "doc3", "document": "content3", "distance": 0.5, "metadata": None},
        ]

        retriever = HybridRetriever(mock_embedding, mock_index)
        results = retriever.retrieve_with_scores("query", threshold=0.5)

        assert len(results) == 2
        assert all(r.distance <= 0.5 for r in results)
        assert [r.distance for r in results] == [0.3, 0.5]

    def test_retrieve_with_scores_default_threshold_is_point_five(self) -> None:
        """Test that default threshold is 0.5."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        mock_embedding.embed.return_value = [0.1]
        mock_index.similarity_search.return_value = [
            {"id": "doc1", "document": "content1", "distance": 0.6, "metadata": None},
        ]

        retriever = HybridRetriever(mock_embedding, mock_index)
        results = retriever.retrieve_with_scores("query")

        assert len(results) == 0

    def test_retrieve_with_scores_empty_list_when_all_above_threshold(self) -> None:
        """Test that empty list is returned when all results exceed threshold."""
        mock_embedding = MagicMock()
        mock_index = MagicMock()
        mock_embedding.embed.return_value = [0.1]
        mock_index.similarity_search.return_value = [
            {"id": "doc1", "document": "content1", "distance": 0.8, "metadata": None},
            {"id": "doc2", "document": "content2", "distance": 0.9, "metadata": None},
        ]

        retriever = HybridRetriever(mock_embedding, mock_index)
        results = retriever.retrieve_with_scores("query", threshold=0.5)

        assert len(results) == 0
