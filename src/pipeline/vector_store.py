"""ChromaDB vector store manager."""

import chromadb
from chromadb.config import Settings

from langchain_chroma import Chroma

from src.pipeline.embedding_service import EmbeddingService


class VectorStoreManager:
    """Manages ChromaDB vector storage with persistence."""

    def __init__(
        self,
        persist_directory: str,
        collection_name: str,
        embedding_service: EmbeddingService,
    ) -> None:
        """Initialize vector store manager.

        Args:
            persist_directory: Directory for ChromaDB persistence.
            collection_name: Name of the collection.
            embedding_service: Service for generating embeddings.
        """
        self._persist_directory = persist_directory
        self._collection_name = collection_name
        self._embedding_service = embedding_service
        self._vector_store: Chroma | None = None

    def check_db_exists(self) -> bool:
        """Check if ChromaDB already exists.

        Returns:
            True if database files exist, False otherwise.
        """
        client = chromadb.PersistentClient(
            path=self._persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        try:
            client.get_collection(name=self._collection_name)
            return True
        except Exception:
            return False

    def check_exists(self) -> bool:
        """Alias for check_db_exists for backwards compatibility."""
        return self.check_db_exists()

    def _create_client(self) -> chromadb.PersistentClient:
        """Create a persistent ChromaDB client.

        Returns:
            ChromaDB PersistentClient instance.
        """
        return chromadb.PersistentClient(
            path=self._persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )

    def delete_collection(self) -> None:
        """Delete the collection if it exists."""
        client = self._create_client()
        try:
            client.delete_collection(name=self._collection_name)
        except Exception:
            pass

    def create_vector_store(
        self,
        documents: list[str],
        metadatas: list[dict] | None = None,
    ) -> Chroma:
        """Create new vector store from documents.

        Args:
            documents: List of text documents.
            metadatas: Optional list of metadata dicts.

        Returns:
            Created Chroma vector store.
        """
        self.delete_collection()
        client = self._create_client()
        embeddings = self._embedding_service.get_embeddings()
        self._vector_store = Chroma.from_texts(
            texts=documents,
            embedding=embeddings,
            client=client,
            collection_name=self._collection_name,
            persist_directory=self._persist_directory,
            metadatas=metadatas,
        )
        return self._vector_store

    def get_vector_store(self) -> Chroma:
        """Get existing vector store.

        Returns:
            Chroma vector store instance.
        """
        if self._vector_store is None:
            client = self._create_client()
            embeddings = self._embedding_service.get_embeddings()
            self._vector_store = Chroma(
                client=client,
                collection_name=self._collection_name,
                embedding_function=embeddings,
            )
        return self._vector_store

    def as_retriever(self, search_kwargs: dict | None = None) -> Chroma:
        """Get vector store as LangChain retriever.

        Args:
            search_kwargs: Optional search parameters, updates defaults.

        Returns:
            Chroma retriever instance.
        """
        vs = self.get_vector_store()
        default = {"k": 3}
        if search_kwargs:
            default.update(search_kwargs)
        return vs.as_retriever(**default)
