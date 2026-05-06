"""Unit tests for pipeline module following TDD methodology."""

from unittest.mock import MagicMock, patch

import pytest

from src.agents.rag_agent import AnswerResult
from src.config import IndexConfig, LlamaCppConfig, RAGConfig
from src.exceptions import PipelineError
from src.indexing.chunker import Chunk
from src.indexing.parser import Document
from src.pipeline import RAGPipeline, PipelineStats, build_pipeline, load_pipeline


class TestPipelineStats:
    """Tests for PipelineStats NamedTuple."""

    def test_pipeline_stats_has_correct_fields(self) -> None:
        """PipelineStats should have documents_processed, chunks_created, embeddings_generated, batches_processed fields."""
        stats = PipelineStats(documents_processed=5, chunks_created=20, embeddings_generated=20, batches_processed=2)

        assert stats.documents_processed == 5
        assert stats.chunks_created == 20
        assert stats.embeddings_generated == 20
        assert stats.batches_processed == 2

    def test_pipeline_stats_is_namedtuple(self) -> None:
        """PipelineStats should be a NamedTuple with positional access."""
        stats = PipelineStats(10, 40, 40, 2)

        assert stats[0] == 10
        assert stats[1] == 40
        assert stats[2] == 40
        assert stats[3] == 2
        assert stats.documents_processed == stats[0]
        assert stats.chunks_created == stats[1]
        assert stats.embeddings_generated == stats[2]
        assert stats.batches_processed == stats[3]


class TestRAGPipelineInit:
    """Tests for RAGPipeline.__init__ method."""

    @patch("src.pipeline.DocumentParser")
    @patch("src.pipeline.TextChunker")
    @patch("src.pipeline.create_embedding")
    @patch("src.pipeline.ChromaIndexManager")
    @patch("src.pipeline.HybridRetriever")
    @patch("src.pipeline.create_llm")
    @patch("src.pipeline.RAGAgent")
    def test_init_creates_all_components(
        self,
        mock_agent_class: MagicMock,
        mock_create_llm: MagicMock,
        mock_hybrid_retriever_class: MagicMock,
        mock_index_manager_class: MagicMock,
        mock_create_embedding: MagicMock,
        mock_chunker_class: MagicMock,
        mock_parser_class: MagicMock,
    ) -> None:
        """RAGPipeline.__init__ should create all required components."""
        config = RAGConfig()

        mock_embedding_instance = MagicMock()
        mock_create_embedding.return_value = mock_embedding_instance

        mock_llm_instance = MagicMock()
        mock_create_llm.return_value = mock_llm_instance

        pipeline = RAGPipeline(config)

        mock_parser_class.assert_called_once()
        mock_chunker_class.assert_called_once_with(
            chunk_size=config.index.chunk_size,
            chunk_overlap=config.index.chunk_overlap,
        )
        mock_create_embedding.assert_called_once_with(config.llamacpp)
        mock_index_manager_class.assert_called_once_with(config.index)
        mock_hybrid_retriever_class.assert_called_once_with(
            embedding_wrapper=mock_embedding_instance,
            index_manager=pipeline.index_manager,
            top_k=config.top_k,
        )
        mock_create_llm.assert_called_once_with(config.llamacpp)
        mock_agent_class.assert_called_once_with(
            retriever=pipeline.retriever,
            llm=mock_llm_instance,
            prompt_template=config.prompt.template,
            system_prompt=config.prompt.system_prompt,
        )

    @patch("src.pipeline.ChromaIndexManager")
    @patch("src.pipeline.create_embedding")
    @patch("src.pipeline.create_llm")
    def test_init_creates_index_with_rag_collection(
        self,
        mock_create_llm: MagicMock,
        mock_create_embedding: MagicMock,
        mock_index_manager_class: MagicMock,
    ) -> None:
        """RAGPipeline.__init__ should create index with 'rag_collection' name."""
        mock_create_embedding.return_value = MagicMock()
        mock_create_llm.return_value = MagicMock()
        mock_index_manager_instance = MagicMock()
        mock_index_manager_class.return_value = mock_index_manager_instance

        config = RAGConfig()
        RAGPipeline(config)

        mock_index_manager_instance.create_index.assert_called_once_with("rag_collection")


class TestRAGPipelineIndexDocuments:
    """Tests for RAGPipeline.index_documents method."""

    @patch("src.pipeline.ChromaIndexManager")
    @patch("src.pipeline.create_embedding")
    @patch("src.pipeline.create_llm")
    def test_index_documents_returns_pipeline_stats(
        self,
        mock_create_llm: MagicMock,
        mock_create_embedding: MagicMock,
        mock_index_manager_class: MagicMock,
    ) -> None:
        """index_documents should return PipelineStats with correct counts."""
        mock_create_embedding.return_value = MagicMock()
        mock_create_llm.return_value = MagicMock()

        pipeline = RAGPipeline(RAGConfig())

        mock_parser = MagicMock()
        mock_doc = Document(source="test.pdf", content="Test content", metadata={})
        mock_parser.parse_directory.return_value = [mock_doc]
        pipeline.parser = mock_parser

        mock_chunker = MagicMock()
        mock_chunk = Chunk(
            content="chunk content",
            source="test.pdf",
            chunk_index=0,
            total_chunks=1,
        )
        mock_chunker.chunk_documents.return_value = [mock_chunk]
        pipeline.chunker = mock_chunker

        mock_embedding = MagicMock()
        mock_embedding.embed_batch.return_value = [[0.1, 0.2, 0.3]]
        pipeline.embedding = mock_embedding

        mock_index_manager = MagicMock()
        pipeline.index_manager = mock_index_manager

        stats = pipeline.index_documents("/some/path")

        assert isinstance(stats, PipelineStats)
        assert stats.documents_processed == 1
        assert stats.chunks_created == 1
        assert stats.embeddings_generated == 1

    @patch("src.pipeline.ChromaIndexManager")
    @patch("src.pipeline.create_embedding")
    @patch("src.pipeline.create_llm")
    def test_index_documents_raises_pipeline_error_on_failure(
        self,
        mock_create_llm: MagicMock,
        mock_create_embedding: MagicMock,
        mock_index_manager_class: MagicMock,
    ) -> None:
        """index_documents should raise PipelineError when indexing fails."""
        mock_create_embedding.return_value = MagicMock()
        mock_create_llm.return_value = MagicMock()

        pipeline = RAGPipeline(RAGConfig())

        mock_parser = MagicMock()
        mock_parser.parse_directory.side_effect = RuntimeError("Parse failed")
        pipeline.parser = mock_parser

        with pytest.raises(PipelineError) as exc_info:
            pipeline.index_documents("/some/path")

        assert "Indexing failed" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, RuntimeError)


class TestRAGPipelineQuery:
    """Tests for RAGPipeline.query method."""

    @patch("src.pipeline.ChromaIndexManager")
    @patch("src.pipeline.create_embedding")
    @patch("src.pipeline.create_llm")
    def test_query_returns_string_answer(
        self,
        mock_create_llm: MagicMock,
        mock_create_embedding: MagicMock,
        mock_index_manager_class: MagicMock,
    ) -> None:
        """query should return a string answer."""
        mock_create_embedding.return_value = MagicMock()
        mock_llm_instance = MagicMock()
        mock_create_llm.return_value = mock_llm_instance

        pipeline = RAGPipeline(RAGConfig())

        mock_agent = MagicMock()
        mock_agent.ask.return_value = "This is the answer"
        pipeline.agent = mock_agent

        result = pipeline.query("What is RAG?")

        assert isinstance(result, str)
        assert result == "This is the answer"
        mock_agent.ask.assert_called_once_with("What is RAG?")


class TestRAGPipelineQueryWithSources:
    """Tests for RAGPipeline.query_with_sources method."""

    @patch("src.pipeline.ChromaIndexManager")
    @patch("src.pipeline.create_embedding")
    @patch("src.pipeline.create_llm")
    def test_query_with_sources_returns_answer_result(
        self,
        mock_create_llm: MagicMock,
        mock_create_embedding: MagicMock,
        mock_index_manager_class: MagicMock,
    ) -> None:
        """query_with_sources should return AnswerResult."""
        mock_create_embedding.return_value = MagicMock()
        mock_create_llm.return_value = MagicMock()

        pipeline = RAGPipeline(RAGConfig())

        expected_result = AnswerResult(
            answer="Test answer",
            sources=["source1.pdf", "source2.pdf"],
            scores=[0.95, 0.89],
        )
        mock_agent = MagicMock()
        mock_agent.ask_with_sources.return_value = expected_result
        pipeline.agent = mock_agent

        result = pipeline.query_with_sources("Explain this")

        assert isinstance(result, AnswerResult)
        assert result.answer == "Test answer"
        assert result.sources == ["source1.pdf", "source2.pdf"]
        assert result.scores == [0.95, 0.89]


class TestBuildPipeline:
    """Tests for build_pipeline factory function."""

    def test_build_pipeline_creates_rag_pipeline(self) -> None:
        """build_pipeline should return a RAGPipeline instance."""
        with patch("src.pipeline.RAGPipeline") as mock_pipeline_class:
            mock_pipeline_instance = MagicMock()
            mock_pipeline_class.return_value = mock_pipeline_instance

            result = build_pipeline()

            mock_pipeline_class.assert_called_once()
            assert result is mock_pipeline_instance

    def test_build_pipeline_with_config(self) -> None:
        """build_pipeline should use provided config."""
        with patch("src.pipeline.RAGPipeline") as mock_pipeline_class:
            mock_pipeline_instance = MagicMock()
            mock_pipeline_class.return_value = mock_pipeline_instance

            config = RAGConfig()
            result = build_pipeline(config)

            mock_pipeline_class.assert_called_once_with(config)
            assert result is mock_pipeline_instance


class TestLoadPipeline:
    """Tests for load_pipeline factory function."""

    @patch("src.pipeline.RAGAgent")
    @patch("src.pipeline.create_llm")
    @patch("src.pipeline.HybridRetriever")
    @patch("src.pipeline.ChromaIndexManager")
    @patch("src.pipeline.create_embedding")
    @patch("src.pipeline.DocumentParser")
    @patch("src.pipeline.TextChunker")
    def test_load_pipeline_creates_rag_pipeline(
        self,
        mock_chunker_class: MagicMock,
        mock_parser_class: MagicMock,
        mock_create_embedding: MagicMock,
        mock_index_manager_class: MagicMock,
        mock_hybrid_retriever_class: MagicMock,
        mock_create_llm: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """load_pipeline should return a RAGPipeline instance with loaded index."""
        mock_create_embedding.return_value = MagicMock()
        mock_create_llm.return_value = MagicMock()
        mock_index_manager_class.load_index.return_value = MagicMock()

        result = load_pipeline()

        assert isinstance(result, RAGPipeline)
        mock_index_manager_class.load_index.assert_called_once()
        mock_parser_class.assert_called_once()
        mock_chunker_class.assert_called_once()
        mock_create_embedding.assert_called_once()
        mock_create_llm.assert_called_once()

    @patch("src.pipeline.RAGAgent")
    @patch("src.pipeline.create_llm")
    @patch("src.pipeline.HybridRetriever")
    @patch("src.pipeline.ChromaIndexManager")
    @patch("src.pipeline.create_embedding")
    @patch("src.pipeline.DocumentParser")
    @patch("src.pipeline.TextChunker")
    def test_load_pipeline_with_config(
        self,
        mock_chunker_class: MagicMock,
        mock_parser_class: MagicMock,
        mock_create_embedding: MagicMock,
        mock_index_manager_class: MagicMock,
        mock_hybrid_retriever_class: MagicMock,
        mock_create_llm: MagicMock,
        mock_agent_class: MagicMock,
    ) -> None:
        """load_pipeline should use provided config and load from persist_directory."""
        mock_create_embedding.return_value = MagicMock()
        mock_create_llm.return_value = MagicMock()
        mock_index_manager_class.load_index.return_value = MagicMock()

        config = RAGConfig()
        result = load_pipeline(config)

        assert isinstance(result, RAGPipeline)
        mock_index_manager_class.load_index.assert_called_once_with(
            config.index.persist_directory, "rag_collection"
        )


class TestPipelineError:
    """Tests for PipelineError exception handling."""

    @patch("src.pipeline.ChromaIndexManager")
    @patch("src.pipeline.create_embedding")
    @patch("src.pipeline.create_llm")
    def test_pipeline_error_contains_cause(
        self,
        mock_create_llm: MagicMock,
        mock_create_embedding: MagicMock,
        mock_index_manager_class: MagicMock,
    ) -> None:
        """PipelineError should chain the original exception."""
        mock_create_embedding.return_value = MagicMock()
        mock_create_llm.return_value = MagicMock()

        pipeline = RAGPipeline(RAGConfig())

        original_error = ValueError("Original error")
        mock_parser = MagicMock()
        mock_parser.parse_directory.side_effect = original_error
        pipeline.parser = mock_parser

        with pytest.raises(PipelineError) as exc_info:
            pipeline.index_documents("/path")

        assert exc_info.value.__cause__ is original_error
        assert "Indexing failed" in str(exc_info.value)