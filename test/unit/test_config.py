"""Tests for src.config module."""

import pytest
from src.config import LlamaCppConfig, IndexConfig, RAGConfig


class TestLlamaCppConfig:
    """Tests for LlamaCppConfig dataclass."""

    def test_default_values(self):
        """Test LlamaCppConfig has correct default values."""
        config = LlamaCppConfig()
        assert config.model_path == "./model/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q6_K.gguf"
        assert config.embedding_model_path == "./model/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"
        assert config.temperature == 0.1
        assert config.n_gpu_layers == -1
        assert config.n_ctx == 12288
        assert config.max_tokens == 2048
        assert config.timeout == 120

    def test_custom_values(self):
        """Test LlamaCppConfig accepts custom values."""
        config = LlamaCppConfig(
            model_path="./custom/model.gguf",
            embedding_model_path="./custom/embedding.gguf",
            temperature=0.5,
            n_gpu_layers=10,
            n_ctx=4096,
            timeout=60,
        )
        assert config.model_path == "./custom/model.gguf"
        assert config.embedding_model_path == "./custom/embedding.gguf"
        assert config.temperature == 0.5
        assert config.n_gpu_layers == 10
        assert config.n_ctx == 4096
        assert config.timeout == 60


class TestIndexConfig:
    """Tests for IndexConfig dataclass."""

    def test_default_values(self):
        """Test IndexConfig has correct default values."""
        config = IndexConfig()
        assert config.chunk_size == 400
        assert config.chunk_overlap == 50
        assert config.persist_directory == "./chroma_db"

    def test_custom_values(self):
        """Test IndexConfig accepts custom values."""
        config = IndexConfig(
            chunk_size=1000,
            chunk_overlap=100,
            persist_directory="/tmp/index",
        )
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 100
        assert config.persist_directory == "/tmp/index"


class TestRAGConfig:
    """Tests for RAGConfig dataclass."""

    def test_default_values(self):
        """Test RAGConfig has correct default values."""
        config = RAGConfig()
        assert config.top_k == 3
        assert config.enable_graph is False

    def test_nested_llamacpp_config_defaults(self):
        """Test RAGConfig has correct nested LlamaCppConfig defaults."""
        config = RAGConfig()
        assert isinstance(config.llamacpp, LlamaCppConfig)
        assert config.llamacpp.model_path == "./model/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q6_K.gguf"
        assert config.llamacpp.embedding_model_path == "./model/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"

    def test_nested_index_config_defaults(self):
        """Test RAGConfig has correct nested IndexConfig defaults."""
        config = RAGConfig()
        assert isinstance(config.index, IndexConfig)
        assert config.index.chunk_size == 400
        assert config.index.persist_directory == "./chroma_db"

    def test_custom_nested_configs(self):
        """Test RAGConfig accepts custom nested configs."""
        llamacpp = LlamaCppConfig(model_path="./custom/model.gguf", temperature=0.9)
        index = IndexConfig(chunk_size=2000, persist_directory="/data/index")
        config = RAGConfig(llamacpp=llamacpp, index=index, top_k=10, enable_graph=True)

        assert config.llamacpp.model_path == "./custom/model.gguf"
        assert config.llamacpp.temperature == 0.9
        assert config.index.chunk_size == 2000
        assert config.index.persist_directory == "/data/index"
        assert config.top_k == 10
        assert config.enable_graph is True

    def test_custom_top_k_and_enable_graph(self):
        """Test RAGConfig custom top_k and enable_graph values."""
        config = RAGConfig(top_k=8, enable_graph=True)
        assert config.top_k == 8
        assert config.enable_graph is True

    def test_nested_configs_are_independent(self):
        """Test that nested configs are independent instances."""
        config1 = RAGConfig()
        config2 = RAGConfig()

        config1.llamacpp.model_path = "./changed/model.gguf"
        config1.index.chunk_size = 999

        assert config2.llamacpp.model_path == "./model/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q6_K.gguf"
        assert config2.index.chunk_size == 400