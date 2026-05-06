"""Hybrid retriever module for vector similarity retrieval."""

from typing import Any, NamedTuple

from src.indexing.vector_index import ChromaIndexManager
from src.models.embedding import LlamaCppEmbeddingWrapper


class RetrievalResult(NamedTuple):
    """Immutable retrieval result container.

    Attributes:
        content: The text content of the retrieved chunk.
        source: Source identifier for the chunk.
        distance: Similarity distance score.
        metadata: Additional metadata about the chunk.
    """

    content: str
    source: str
    distance: float
    metadata: dict[str, Any] | None = None


class HybridRetriever:
    """Hybrid retriever combining embedding and vector search.

    This class handles retrieving relevant documents based on
    semantic similarity using embeddings and ChromaDB.

    Attributes:
        embedding_wrapper: Wrapper for embedding model.
        index_manager: ChromaDB index manager.
        top_k: Number of results to retrieve.
    """

    def __init__(
        self,
        embedding_wrapper: LlamaCppEmbeddingWrapper,
        index_manager: ChromaIndexManager,
        top_k: int = 4,
    ) -> None:
        """Initialize HybridRetriever.

        Args:
            embedding_wrapper: Ollama embedding wrapper.
            index_manager: ChromaDB index manager.
            top_k: Number of results to retrieve.
        """
        self.embedding_wrapper = embedding_wrapper
        self.index_manager = index_manager
        self.top_k = top_k

    def retrieve(self, query: str) -> list[RetrievalResult]:
        """Retrieve relevant chunks for a query.

        Args:
            query: The search query.

        Returns:
            List of RetrievalResult namedtuples.

        Raises:
            RetrievalError: If retrieval fails.
        """
        from src.exceptions import RetrievalError

        try:
            query_embedding = self.embedding_wrapper.embed(query)
            results = self.index_manager.similarity_search(
                query_embedding, top_k=self.top_k
            )

            return [
                RetrievalResult(
                    content=r["document"],
                    source=r["id"].split("_")[0] if "_" in r["id"] else r["id"],
                    distance=r["distance"],
                    metadata=r["metadata"],
                )
                for r in results
            ]
        except Exception as e:
            raise RetrievalError(f"Retrieval failed: {e}") from e

    def retrieve_with_scores(
        self, query: str, threshold: float = 0.5
    ) -> list[RetrievalResult]:
        """Retrieve chunks with distance threshold filtering.

        Args:
            query: The search query.
            threshold: Maximum distance threshold.

        Returns:
            List of RetrievalResult within distance threshold.
        """
        results = self.retrieve(query)
        return [r for r in results if r.distance <= threshold]