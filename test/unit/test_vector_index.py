"""Tests for src.indexing.vector_index module."""

from unittest.mock import MagicMock, patch

import pytest

from src.config import IndexConfig
from src.exceptions import IndexError
from src.indexing.vector_index import ChromaIndexManager, create_index_manager


class TestChromaIndexManagerInit:
    """Tests for ChromaIndexManager.__init__."""

    def test_init_creates_persistent_client(self) -> None:
        """Test that __init__ creates a ChromaDB PersistentClient."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_chromadb.PersistentClient.return_value = MagicMock()
            config = IndexConfig()
            manager = ChromaIndexManager(config)
            mock_chromadb.PersistentClient.assert_called_once()

    def test_init_stores_config(self) -> None:
        """Test that __init__ stores the config."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_chromadb.PersistentClient.return_value = MagicMock()
            config = IndexConfig(persist_directory="/test/path")
            manager = ChromaIndexManager(config)
            assert manager.config == config

    def test_init_sets_collection_to_none(self) -> None:
        """Test that __init__ initializes _collection to None."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_chromadb.PersistentClient.return_value = MagicMock()
            config = IndexConfig()
            manager = ChromaIndexManager(config)
            assert manager._collection is None


class TestChromaIndexManagerCreateIndex:
    """Tests for ChromaIndexManager.create_index."""

    def test_create_index_creates_collection(self) -> None:
        """Test that create_index creates a collection with correct name."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_client.create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            config = IndexConfig()
            manager = ChromaIndexManager(config)
            manager.create_index("test_collection")

            mock_client.reset.assert_called_once()
            mock_client.create_collection.assert_called_once_with(
                name="test_collection",
                metadata={"hnsw:space": "cosine"},
            )

    def test_create_index_stores_collection(self) -> None:
        """Test that create_index stores the collection."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_client.create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            config = IndexConfig()
            manager = ChromaIndexManager(config)
            manager.create_index("test_collection")

            assert manager._collection == mock_collection

    def test_create_index_raises_index_error_on_failure(self) -> None:
        """Test that create_index raises IndexError on failure."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_client = MagicMock()
            mock_client.reset.side_effect = Exception("Connection failed")
            mock_chromadb.PersistentClient.return_value = mock_client

            config = IndexConfig()
            manager = ChromaIndexManager(config)

            with pytest.raises(IndexError, match="Failed to create index"):
                manager.create_index()


class TestChromaIndexManagerAddChunks:
    """Tests for ChromaIndexManager.add_chunks."""

    def test_add_chunks_calls_collection_add(self) -> None:
        """Test that add_chunks calls collection.add with correct args."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_client.create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            config = IndexConfig()
            manager = ChromaIndexManager(config)
            manager.create_index("test_collection")

            embeddings = [[0.1, 0.2], [0.3, 0.4]]
            documents = ["doc1", "doc2"]
            ids = ["id1", "id2"]
            metadatas = [{"source": "test"}]

            manager.add_chunks(embeddings, documents, ids, metadatas)

            mock_collection.add.assert_called_once_with(
                embeddings=embeddings,
                documents=documents,
                ids=ids,
                metadatas=metadatas,
            )

    def test_add_chunks_raises_error_when_index_not_created(self) -> None:
        """Test that add_chunks raises IndexError if index not created."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_client = MagicMock()
            mock_chromadb.PersistentClient.return_value = mock_client

            config = IndexConfig()
            manager = ChromaIndexManager(config)

            with pytest.raises(IndexError, match="Index not created"):
                manager.add_chunks([], [], [])

    def test_add_chunks_raises_index_error_on_failure(self) -> None:
        """Test that add_chunks raises IndexError on collection add failure."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_collection.add.side_effect = Exception("Add failed")
            mock_client.create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            config = IndexConfig()
            manager = ChromaIndexManager(config)
            manager.create_index("test_collection")

            with pytest.raises(IndexError, match="Failed to add chunks"):
                manager.add_chunks([], [], [])


class TestChromaIndexManagerSimilaritySearch:
    """Tests for ChromaIndexManager.similarity_search."""

    def test_similarity_search_returns_formatted_results(self) -> None:
        """Test that similarity_search returns properly formatted results."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_client.create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            mock_collection.query.return_value = {
                "ids": [["id1", "id2"]],
                "documents": [["doc1", "doc2"]],
                "distances": [[0.1, 0.2]],
                "metadatas": [[{"source": "test1"}, {"source": "test2"}]],
            }

            config = IndexConfig()
            manager = ChromaIndexManager(config)
            manager.create_index("test_collection")

            results = manager.similarity_search([0.1, 0.2], top_k=2)

            assert len(results) == 2
            assert results[0]["id"] == "id1"
            assert results[0]["document"] == "doc1"
            assert results[0]["distance"] == 0.1
            assert results[0]["metadata"] == {"source": "test1"}

    def test_similarity_search_raises_error_when_index_not_created(self) -> None:
        """Test that similarity_search raises IndexError if index not created."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_client = MagicMock()
            mock_chromadb.PersistentClient.return_value = mock_client

            config = IndexConfig()
            manager = ChromaIndexManager(config)

            with pytest.raises(IndexError, match="Index not created"):
                manager.similarity_search([0.1, 0.2])

    def test_similarity_search_raises_index_error_on_failure(self) -> None:
        """Test that similarity_search raises IndexError on query failure."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_collection.query.side_effect = Exception("Query failed")
            mock_client.create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            config = IndexConfig()
            manager = ChromaIndexManager(config)
            manager.create_index("test_collection")

            with pytest.raises(IndexError, match="Similarity search failed"):
                manager.similarity_search([0.1, 0.2])


class TestChromaIndexManagerPersist:
    """Tests for ChromaIndexManager.persist."""

    def test_persist_is_callable(self) -> None:
        """Test that persist method is callable without error."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_client = MagicMock()
            mock_chromadb.PersistentClient.return_value = mock_client

            config = IndexConfig()
            manager = ChromaIndexManager(config)
            manager.persist()


class TestCreateIndexManager:
    """Tests for create_index_manager factory function."""

    def test_create_index_manager_returns_manager(self) -> None:
        """Test that factory returns ChromaIndexManager instance."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_client.create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            config = IndexConfig()
            manager = create_index_manager(config, "test_collection")

            assert isinstance(manager, ChromaIndexManager)

    def test_create_index_manager_uses_default_config(self) -> None:
        """Test that factory uses default config when none provided."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_client.create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            manager = create_index_manager(collection_name="test_collection")

            assert isinstance(manager, ChromaIndexManager)
            assert manager.config is not None

    def test_create_index_manager_creates_index(self) -> None:
        """Test that factory creates the index."""
        with patch("src.indexing.vector_index.chromadb") as mock_chromadb:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_client.create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            config = IndexConfig()
            manager = create_index_manager(config, "my_collection")

            mock_client.create_collection.assert_called_once_with(
                name="my_collection",
                metadata={"hnsw:space": "cosine"},
            )