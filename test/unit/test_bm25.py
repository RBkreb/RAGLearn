"""Unit tests for BM25Retriever."""

import pytest
from unittest.mock import MagicMock, patch

from src.utils.bm25 import BM25Retriever, tokenize


class TestTokenize:
    """Tests for tokenize function."""

    def test_tokenize_single_string(self) -> None:
        """Test tokenizing a single string."""
        result = tokenize("今天天气晴朗")
        assert result is not None
        assert len(result.ids) == 1

    def test_tokenize_list_of_strings(self) -> None:
        """Test tokenizing a list of strings."""
        texts = ["今天天气晴朗", "小明和小红一起上学"]
        result = tokenize(texts)
        assert len(result.ids) == 2

    def test_tokenize_returns_ids(self) -> None:
        """Test tokenize returns token IDs by default."""
        result = tokenize("测试文本")
        assert result.ids is not None
        assert all(isinstance(ids, list) for ids in result.ids)


class TestBM25Retriever:
    """Tests for BM25Retriever class."""

    def test_init_empty_corpus(self) -> None:
        """Test initialization with empty corpus."""
        retriever = BM25Retriever()
        assert retriever._corpus == []
        assert retriever._retriever is None

    def test_init_with_corpus(self) -> None:
        """Test initialization with corpus."""
        corpus = ["今天天气晴朗", "小明和小红一起上学"]
        retriever = BM25Retriever(corpus)
        assert retriever._corpus == corpus

    def test_index_builds_index(self) -> None:
        """Test index method builds BM25 index."""
        corpus = ["今天天气晴朗", "小明和小红一起上学", "我们一起学猫叫"]
        retriever = BM25Retriever(corpus)
        retriever.index()
        assert retriever._retriever is not None

    def test_index_empty_corpus_raises(self) -> None:
        """Test indexing empty corpus raises error."""
        retriever = BM25Retriever()
        with pytest.raises(ValueError, match="No corpus"):
            retriever.index()

    def test_index_with_corpus_parameter(self) -> None:
        """Test index with corpus parameter."""
        retriever = BM25Retriever()
        corpus = ["今天天气晴朗"]
        retriever.index(corpus)
        assert retriever._corpus == corpus
        assert retriever._retriever is not None

    def test_retrieve_returns_results(self) -> None:
        """Test retrieve returns documents and scores."""
        corpus = ["今天天气晴朗", "小明和小红一起上学", "我们一起学猫叫"]
        retriever = BM25Retriever(corpus)
        retriever.index()

        docs, scores = retriever.retrieve("天气", k=2)
        assert len(docs) == 2
        assert len(scores) == 2
        assert all(isinstance(d, str) for d in docs)
        assert all(isinstance(s, (int, float)) for s in scores)

    def test_retrieve_without_index_raises(self) -> None:
        """Test retrieve without index raises error."""
        retriever = BM25Retriever()
        with pytest.raises(ValueError, match="No index"):
            retriever.retrieve("测试")

    @patch("src.utils.bm25.BM25")
    def test_index_from_chroma(self, mock_bm25: MagicMock) -> None:
        """Test indexing from ChromaDB collection."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "documents": ["今天天气晴朗", "小明和小红一起上学"]
        }

        mock_chroma = MagicMock()
        mock_chroma.get_collection.return_value = mock_collection

        retriever = BM25Retriever()
        retriever.set_chroma(mock_chroma, "test_collection")
        retriever.index_from_chroma()

        mock_chroma.get_collection.assert_called_once_with("test_collection")
        assert retriever._corpus == ["今天天气晴朗", "小明和小红一起上学"]

    def test_index_from_chroma_no_client_raises(self) -> None:
        """Test index_from_chroma without client raises error."""
        retriever = BM25Retriever()
        with pytest.raises(ValueError, match="No ChromaDB client"):
            retriever.index_from_chroma()

    def test_save_creates_files(self, tmp_path: MagicMock) -> None:
        """Test save creates index files."""
        corpus = ["今天天气晴朗"]
        retriever = BM25Retriever(corpus)
        retriever.index()

        save_path = str(tmp_path / "bm25_index")
        retriever.save(save_path)

        import os
        assert os.path.exists(os.path.join(save_path, "corpus.txt"))

    def test_save_without_index_raises(self) -> None:
        """Test save without index raises error."""
        retriever = BM25Retriever()
        with pytest.raises(ValueError, match="No index"):
            retriever.save("/tmp/test")

    def test_load_from_disk(self, tmp_path: MagicMock) -> None:
        """Test loading index from disk."""
        save_path = str(tmp_path / "bm25_index")
        corpus = ["今天天气晴朗", "小明和小红一起上学"]

        retriever = BM25Retriever(corpus)
        retriever.index()
        retriever.save(save_path)

        loaded = BM25Retriever.load(save_path)
        assert loaded._corpus == corpus

    def test_load_with_override_corpus(self, tmp_path: MagicMock) -> None:
        """Test loading with corpus override."""
        save_path = str(tmp_path / "bm25_index")
        original_corpus = ["今天天气晴朗"]

        retriever = BM25Retriever(original_corpus)
        retriever.index()
        retriever.save(save_path)

        new_corpus = ["新文档"]
        loaded = BM25Retriever.load(save_path, corpus=new_corpus)
        assert loaded._corpus == new_corpus