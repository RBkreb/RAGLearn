"""Unit tests for vector store manager."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline.embedding_service import EmbeddingService
from src.pipeline.vector_store import VectorStoreManager


class TestVectorStoreManager:
    """Tests for VectorStoreManager class."""

    @pytest.fixture
    def mock_embedding_service(self) -> MagicMock:
        """Create a mock EmbeddingService."""
        mock_service = MagicMock(spec=EmbeddingService)
        mock_embeddings = MagicMock()
        mock_service.get_embeddings.return_value = mock_embeddings
        return mock_service

    @pytest.fixture
    def vector_store_manager(
        self, mock_embedding_service: MagicMock
    ) -> VectorStoreManager:
        """Create a VectorStoreManager instance with mocked dependencies."""
        return VectorStoreManager(
            persist_directory="/test/chroma_db",
            collection_name="test_collection",
            embedding_service=mock_embedding_service,
        )

    def test_initialization_stores_persist_directory(
        self, vector_store_manager: VectorStoreManager
    ) -> None:
        """Should store persist_directory."""
        assert vector_store_manager._persist_directory == "/test/chroma_db"

    def test_initialization_stores_collection_name(
        self, vector_store_manager: VectorStoreManager
    ) -> None:
        """Should store collection_name."""
        assert vector_store_manager._collection_name == "test_collection"

    def test_initialization_stores_embedding_service(
        self, vector_store_manager: VectorStoreManager, mock_embedding_service: MagicMock
    ) -> None:
        """Should store embedding_service."""
        assert vector_store_manager._embedding_service is mock_embedding_service

    def test_initialization_sets_vector_store_to_none(
        self, vector_store_manager: VectorStoreManager
    ) -> None:
        """Should initialize _vector_store as None."""
        assert vector_store_manager._vector_store is None

    @patch("src.pipeline.vector_store.chromadb.PersistentClient")
    def test_check_db_exists_returns_true_when_file_exists(
        self, mock_client_class: MagicMock, vector_store_manager: VectorStoreManager
    ) -> None:
        """Should return True when collection exists."""
        mock_client = MagicMock()
        mock_client.get_collection.return_value = MagicMock()
        mock_client_class.return_value = mock_client

        result = vector_store_manager.check_db_exists()

        assert result is True
        mock_client.get_collection.assert_called_once_with(name="test_collection")

    @patch("src.pipeline.vector_store.chromadb.PersistentClient")
    def test_check_db_exists_returns_false_when_file_not_exists(
        self, mock_client_class: MagicMock, vector_store_manager: VectorStoreManager
    ) -> None:
        """Should return False when collection does not exist."""
        mock_client = MagicMock()
        mock_client.get_collection.side_effect = Exception("not found")
        mock_client_class.return_value = mock_client

        result = vector_store_manager.check_db_exists()

        assert result is False

    @patch("src.pipeline.vector_store.chromadb.PersistentClient")
    def test_check_exists_calls_check_db_exists(
        self,
        mock_client_class: MagicMock,
        vector_store_manager: VectorStoreManager,
    ) -> None:
        """Should have check_exists call check_db_exists."""
        mock_client = MagicMock()
        mock_client.get_collection.return_value = MagicMock()
        mock_client_class.return_value = mock_client

        result = vector_store_manager.check_exists()

        assert result is True
        mock_client.get_collection.assert_called_once()

    @patch("src.pipeline.vector_store.Chroma")
    def test_create_vector_store_calls_embedding_service(
        self,
        mock_chroma_class: MagicMock,
        vector_store_manager: VectorStoreManager,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Should call get_embeddings on embedding_service."""
        mock_vs = MagicMock()
        mock_chroma_class.from_texts.return_value = mock_vs

        vector_store_manager.create_vector_store(documents=["doc1", "doc2"])

        mock_embedding_service.get_embeddings.assert_called_once()

    @patch("src.pipeline.vector_store.Chroma")
    def test_create_vector_store_creates_chroma_with_documents(
        self,
        mock_chroma_class: MagicMock,
        vector_store_manager: VectorStoreManager,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Should create Chroma vector store with documents."""
        mock_vs = MagicMock()
        mock_chroma_class.from_texts.return_value = mock_vs
        mock_embeddings = MagicMock()
        mock_embedding_service.get_embeddings.return_value = mock_embeddings

        vector_store_manager.create_vector_store(
            documents=["doc1", "doc2"],
            metadatas=[{"source": "file1"}, {"source": "file2"}]
        )

        mock_chroma_class.from_texts.assert_called_once()
        call_kwargs = mock_chroma_class.from_texts.call_args.kwargs
        assert call_kwargs["texts"] == ["doc1", "doc2"]
        assert call_kwargs["embedding"] is mock_embeddings
        assert call_kwargs["persist_directory"] == "/test/chroma_db"
        assert call_kwargs["collection_name"] == "test_collection"
        assert call_kwargs["metadatas"] == [{"source": "file1"}, {"source": "file2"}]

    @patch("src.pipeline.vector_store.Chroma")
    def test_create_vector_store_returns_chroma_instance(
        self,
        mock_chroma_class: MagicMock,
        vector_store_manager: VectorStoreManager,
    ) -> None:
        """Should return Chroma vector store instance."""
        mock_vs = MagicMock()
        mock_chroma_class.from_texts.return_value = mock_vs

        result = vector_store_manager.create_vector_store(documents=["doc1"])

        assert result is mock_vs

    @patch("src.pipeline.vector_store.Chroma")
    def test_create_vector_store_caches_vector_store(
        self,
        mock_chroma_class: MagicMock,
        vector_store_manager: VectorStoreManager,
    ) -> None:
        """Should store created vector store in _vector_store."""
        mock_vs = MagicMock()
        mock_chroma_class.from_texts.return_value = mock_vs

        vector_store_manager.create_vector_store(documents=["doc1"])

        assert vector_store_manager._vector_store is mock_vs

    @patch("src.pipeline.vector_store.Chroma")
    def test_get_vector_store_returns_existing_when_cached(
        self,
        mock_chroma_class: MagicMock,
        vector_store_manager: VectorStoreManager,
    ) -> None:
        """Should return cached vector store without creating new one."""
        mock_vs = MagicMock()
        vector_store_manager._vector_store = mock_vs

        result = vector_store_manager.get_vector_store()

        assert result is mock_vs
        mock_chroma_class.assert_not_called()

    @patch("src.pipeline.vector_store.Chroma")
    def test_get_vector_store_creates_new_when_none(
        self,
        mock_chroma_class: MagicMock,
        vector_store_manager: VectorStoreManager,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Should create new Chroma when _vector_store is None."""
        mock_vs = MagicMock()
        mock_chroma_class.return_value = mock_vs
        mock_embeddings = MagicMock()
        mock_embedding_service.get_embeddings.return_value = mock_embeddings

        result = vector_store_manager.get_vector_store()

        assert result is mock_vs
        mock_chroma_class.assert_called_once()

    @patch("src.pipeline.vector_store.chromadb.PersistentClient")
    def test_get_vector_store_uses_persistent_client(
        self,
        mock_client_class: MagicMock,
        vector_store_manager: VectorStoreManager,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Should create PersistentClient with persist_directory."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_vs = MagicMock()
        mock_embeddings = MagicMock()
        mock_embedding_service.get_embeddings.return_value = mock_embeddings

        vector_store_manager.get_vector_store()

        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args.kwargs
        assert call_kwargs["path"] == "/test/chroma_db"

    @patch("src.pipeline.vector_store.Chroma")
    def test_as_retriever_calls_get_vector_store(
        self,
        mock_chroma_class: MagicMock,
        vector_store_manager: VectorStoreManager,
    ) -> None:
        """Should call get_vector_store to get the store."""
        mock_vs = MagicMock()
        mock_vs.as_retriever.return_value = MagicMock()
        mock_chroma_class.return_value = mock_vs

        vector_store_manager.as_retriever()

        mock_vs.as_retriever.assert_called_once()

    @patch("src.pipeline.vector_store.Chroma")
    def test_as_retriever_uses_default_k_param(
        self,
        mock_chroma_class: MagicMock,
        vector_store_manager: VectorStoreManager,
    ) -> None:
        """Should use default k=4 when no search_kwargs provided."""
        mock_vs = MagicMock()
        mock_vs.as_retriever.return_value = MagicMock()
        mock_chroma_class.return_value = mock_vs

        vector_store_manager.as_retriever()

        mock_vs.as_retriever.assert_called_once_with(k=4)

    @patch("src.pipeline.vector_store.Chroma")
    def test_as_retriever_updates_default_with_search_kwargs(
        self,
        mock_chroma_class: MagicMock,
        vector_store_manager: VectorStoreManager,
    ) -> None:
        """Should update default k=4 with custom search_kwargs."""
        mock_vs = MagicMock()
        mock_vs.as_retriever.return_value = MagicMock()
        mock_chroma_class.return_value = mock_vs

        vector_store_manager.as_retriever(search_kwargs={"k": 10})

        mock_vs.as_retriever.assert_called_once_with(k=10)

    @patch("src.pipeline.vector_store.Chroma")
    def test_as_retriever_merges_search_kwargs_with_defaults(
        self,
        mock_chroma_class: MagicMock,
        vector_store_manager: VectorStoreManager,
    ) -> None:
        """Should merge custom search_kwargs with defaults."""
        mock_vs = MagicMock()
        mock_vs.as_retriever.return_value = MagicMock()
        mock_chroma_class.return_value = mock_vs

        vector_store_manager.as_retriever(search_kwargs={"filter": "category"})

        mock_vs.as_retriever.assert_called_once_with(k=4, filter="category")

    @patch("src.pipeline.vector_store.Chroma")
    def test_as_retriever_returns_retriever(
        self,
        mock_chroma_class: MagicMock,
        vector_store_manager: VectorStoreManager,
    ) -> None:
        """Should return result of as_retriever call."""
        mock_vs = MagicMock()
        mock_retriever = MagicMock()
        mock_vs.as_retriever.return_value = mock_retriever
        mock_chroma_class.return_value = mock_vs

        result = vector_store_manager.as_retriever()

        assert result is mock_retriever
