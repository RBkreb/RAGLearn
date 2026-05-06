"""Main RAG pipeline orchestration."""

from __future__ import annotations

from typing import NamedTuple

from src.agents.rag_agent import AnswerResult, RAGAgent
from src.config import IndexConfig, LlamaCppConfig, RAGConfig
from src.indexing.chunker import Chunk, TextChunker
from src.indexing.parser import Document, DocumentParser
from src.indexing.vector_index import ChromaIndexManager
from src.monitoring.memory_monitor import MemoryMonitor
from src.models.embedding import LlamaCppEmbeddingWrapper, create_embedding
from src.models.llm import LlamaCppLLMWrapper, create_llm
from src.retrieval.hybrid_retriever import HybridRetriever

DEFAULT_BATCH_SIZE = 100


class PipelineStats(NamedTuple):
    """Statistics from pipeline indexing operation.

    Attributes:
        documents_processed: Number of documents processed.
        chunks_created: Number of chunks created.
        embeddings_generated: Number of embeddings generated.
        batches_processed: Number of batches processed.
    """

    documents_processed: int
    chunks_created: int
    embeddings_generated: int
    batches_processed: int


class RAGPipeline:
    """Main RAG pipeline orchestrating all components.

    This class coordinates document parsing, chunking, indexing,
    retrieval, and answer generation.

    Attributes:
        config: RAG configuration dataclass.
        parser: Document parser.
        chunker: Text chunker.
        embedding: Embedding wrapper.
        index_manager: ChromaDB index manager.
        retriever: Hybrid retriever.
        agent: RAG agent.
    """

    def __init__(self, config: RAGConfig) -> None:
        """Initialize RAG pipeline.

        Args:
            config: RAG configuration dataclass.
        """
        self.config = config
        self.parser = DocumentParser()
        self.chunker = TextChunker(
            chunk_size=config.index.chunk_size,
            chunk_overlap=config.index.chunk_overlap,
        )
        self.embedding = create_embedding(config.llamacpp)
        self.index_manager = ChromaIndexManager(config.index)
        self.index_manager.create_index("rag_collection")

        self.retriever = HybridRetriever(
            embedding_wrapper=self.embedding,
            index_manager=self.index_manager,
            top_k=config.top_k,
        )
        self.llm = create_llm(config.llamacpp)
        self.agent = RAGAgent(
            retriever=self.retriever,
            llm=self.llm,
            prompt_template=config.prompt.template,
            system_prompt=config.prompt.system_prompt,
        )

    def index_documents(
        self,
        directory: str,
        batch_size: int = DEFAULT_BATCH_SIZE,
        memory_threshold_mb: float = 500.0,
    ) -> PipelineStats:
        """Index all documents from a directory using batch processing.

        Args:
            directory: Path to the directory containing documents.
            batch_size: Number of chunks to process per batch.
            memory_threshold_mb: Memory threshold for leak detection.

        Returns:
            PipelineStats with indexing statistics.

        Raises:
            PipelineError: If indexing fails.
        """
        from src.exceptions import PipelineError

        monitor = MemoryMonitor(threshold_mb=memory_threshold_mb)

        try:
            monitor.start()
            documents = self.parser.parse_directory(directory)
            chunks = self.chunker.chunk_documents(documents)

            total_embeddings = 0
            batches_processed = 0

            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]

                embeddings = self.embedding.embed_batch([c.content for c in batch])
                total_embeddings += len(embeddings)

                chunk_ids = [f"{c.source}_{c.chunk_index}" for c in batch]
                metadatas = [
                    {
                        "source": c.source,
                        "chunk_index": c.chunk_index,
                        "total_chunks": c.total_chunks,
                    }
                    for c in batch
                ]

                self.index_manager.add_chunks(
                    embeddings=embeddings,
                    documents=[c.content for c in batch],
                    ids=chunk_ids,
                    metadatas=metadatas,
                )

                del embeddings
                batches_processed += 1

                snap = monitor.take_snapshot(f"batch_{batches_processed}")
                warning = monitor.get_leak_warning()
                if warning:
                    import logging
                    logging.warning(warning)

            return PipelineStats(
                documents_processed=len(documents),
                chunks_created=len(chunks),
                embeddings_generated=total_embeddings,
                batches_processed=batches_processed,
            )
        except Exception as e:
            raise PipelineError(f"Indexing failed: {e}") from e
        finally:
            monitor.stop()

    def query(self, question: str) -> str:
        """Query the RAG pipeline.

        Args:
            question: The user's question.

        Returns:
            The generated answer as a string.
        """
        return self.agent.ask(question)

    def query_with_sources(self, question: str) -> AnswerResult:
        """Query with source information.

        Args:
            question: The user's question.

        Returns:
            AnswerResult with answer, sources, and scores.
        """
        return self.agent.ask_with_sources(question)


def build_pipeline(config: RAGConfig | None = None) -> RAGPipeline:
    """Factory function to build a RAG pipeline.

    Args:
        config: Optional RAG configuration. Uses defaults if not provided.

    Returns:
        Configured RAGPipeline instance.
    """
    if config is None:
        config = RAGConfig()
    return RAGPipeline(config)


def load_pipeline(config: RAGConfig | None = None) -> RAGPipeline:
    """Load an existing RAG pipeline from persisted index.

    Args:
        config: Optional RAG configuration. Uses defaults if not provided.

    Returns:
        RAGPipeline instance ready for querying.
    """
    if config is None:
        config = RAGConfig()

    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.config = config
    pipeline.parser = DocumentParser()
    pipeline.chunker = TextChunker(
        chunk_size=config.index.chunk_size,
        chunk_overlap=config.index.chunk_overlap,
    )
    pipeline.embedding = create_embedding(config.llamacpp)
    pipeline.index_manager = ChromaIndexManager.load_index(
        config.index.persist_directory, "rag_collection"
    )
    pipeline.retriever = HybridRetriever(
        embedding_wrapper=pipeline.embedding,
        index_manager=pipeline.index_manager,
        top_k=config.top_k,
    )
    pipeline.llm = create_llm(config.llamacpp)
    pipeline.agent = RAGAgent(
        retriever=pipeline.retriever,
        llm=pipeline.llm,
        prompt_template=config.prompt.template,
        system_prompt=config.prompt.system_prompt,
    )

    return pipeline