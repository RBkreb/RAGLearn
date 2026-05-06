"""ChromaDB vector index manager."""

from __future__ import annotations

from typing import Any

import chromadb
from chromadb.config import Settings

from src.config import IndexConfig
from src.exceptions import IndexError


class ChromaIndexManager:
    """Manager for ChromaDB vector index operations.

    This class handles creating, persisting, and querying ChromaDB
    vector indices for the RAG pipeline.

    Attributes:
        config: Index configuration dataclass.
        _client: The underlying ChromaDB client.
        _collection: The vector collection.
        _persist_directory: Directory for persistent storage.
    """

    def __init__(self, config: IndexConfig) -> None:
        """Initialize ChromaDB index manager.

        Args:
            config: Index configuration including persist_directory.
        """
        self.config = config
        self._persist_directory = config.persist_directory
        self._client = chromadb.PersistentClient(
            path=self._persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        self._collection: Any = None

    @classmethod
    def load_index(
        cls, persist_directory: str, collection_name: str = "rag_collection"
    ) -> "ChromaIndexManager":
        """Load an existing persisted index.

        Args:
            persist_directory: Directory where the index was persisted.
            collection_name: Name of the collection to load.

        Returns:
            ChromaIndexManager instance with loaded index.

        Raises:
            IndexError: If loading fails or collection doesn't exist.
        """
        config = IndexConfig(persist_directory=persist_directory)
        manager = cls(config)
        try:
            manager._collection = manager._client.get_collection(name=collection_name)
        except Exception as e:
            raise IndexError(
                f"Failed to load collection '{collection_name}': {e}"
            ) from e
        return manager

    def __enter__(self) -> "ChromaIndexManager":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and close resources."""
        self.close()

    def close(self) -> None:
        """Close and cleanup resources."""
        self._collection = None
        self._client = None

    def create_index(self, collection_name: str = "rag_collection") -> None:
        """Create or reset a vector index collection.

        Args:
            collection_name: Name of the collection to create.
        """
        try:
            self._client.reset()
            self._collection = self._client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            raise IndexError(f"Failed to create index: {e}") from e

    def get_or_create_index(
        self, collection_name: str = "rag_collection"
    ) -> None:
        """Get or create a vector index collection.

        Use this method when you want to load existing index if present,
        or create a new one if not.

        Args:
            collection_name: Name of the collection.
        """
        try:
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            raise IndexError(f"Failed to get or create index: {e}") from e

    def add_chunks(
        self,
        embeddings: list[list[float]],
        documents: list[str],
        ids: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add chunks to the vector index.

        Args:
            embeddings: List of embedding vectors.
            documents: List of text documents.
            ids: List of unique identifiers for each chunk.
            metadatas: Optional list of metadata dictionaries.

        Raises:
            IndexError: If adding chunks fails.
        """
        if self._collection is None:
            raise IndexError("Index not created. Call create_index first.")

        try:
            self._collection.add(
                embeddings=embeddings,
                documents=documents,
                ids=ids,
                metadatas=metadatas,
            )
        except Exception as e:
            raise IndexError(f"Failed to add chunks: {e}") from e

    def similarity_search(
        self, query_embedding: list[float], top_k: int = 4
    ) -> list[dict[str, Any]]:
        """Search for similar chunks.

        Args:
            query_embedding: Query embedding vector.
            top_k: Number of results to return.

        Returns:
            List of result dictionaries with documents, distances, and metadata.

        Raises:
            IndexError: If search fails.
        """
        if self._collection is None:
            raise IndexError("Index not created. Call create_index first.")

        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )

            return [
                {
                    "id": rid,
                    "document": doc,
                    "distance": dist,
                    "metadata": meta,
                }
                for rid, doc, dist, meta in zip(
                    results.get("ids", [[]])[0],
                    results.get("documents", [[]])[0],
                    results.get("distances", [[]])[0],
                    results.get("metadatas", [[{}]])[0],
                )
            ]
        except Exception as e:
            raise IndexError(f"Similarity search failed: {e}") from e

    def persist(self) -> None:
        """Persist the index to disk.

        Note: PersistentClient auto-persists, but this method
        is provided for interface consistency.
        """
        # PersistentClient handles auto-persistence, no action needed


def create_index_manager(
    config: IndexConfig | None = None, collection_name: str = "rag_collection"
) -> ChromaIndexManager:
    """Factory function to create a ChromaIndexManager.

    Args:
        config: Optional index configuration. Uses defaults if not provided.
        collection_name: Name of the collection to create.

    Returns:
        Configured ChromaIndexManager instance.
    """
    if config is None:
        config = IndexConfig()
    manager = ChromaIndexManager(config)
    manager.create_index(collection_name)
    return manager


def load_index_manager(
    persist_directory: str, collection_name: str = "rag_collection"
) -> ChromaIndexManager:
    """Factory function to load an existing ChromaIndexManager.

    Args:
        persist_directory: Directory where the index was persisted.
        collection_name: Name of the collection to load.

    Returns:
        ChromaIndexManager instance with loaded index.
    """
    return ChromaIndexManager.load_index(persist_directory, collection_name)