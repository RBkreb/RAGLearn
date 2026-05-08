"""RAG pipeline orchestrator."""
import os
import logging

os.environ.update({
    "LLAMA_VERBOSE": "0",
    "HF_HUB_VERBOSITY": "error",
    "VLLM_LOGGING_LEVEL": "ERROR",
    "TRANSFORMERS_VERBOSITY": "error"
})
 
logging.basicConfig(level=logging.ERROR)
for name in ["transformers", "huggingface_hub", "llama", "vllm", "accelerate","ggml"]:
    logging.getLogger(name).setLevel(logging.ERROR)

from pathlib import Path

from src.config import PipelineConfig, get_config
from src.pipeline.document_loader import load_documents
from src.pipeline.text_chunker import chunk_documents
from src.pipeline.embedding_service import EmbeddingService
from src.pipeline.vector_store import VectorStoreManager


class RAGPipeline:
    """Standalone RAG pipeline for document embedding and retrieval."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        """Initialize RAG pipeline.

        Args:
            config: Pipeline configuration. Uses default if not provided.
        """
        self._config = config or PipelineConfig()
        self._embedding_service = EmbeddingService(
            model_path=self._config.embedding_model_path,
            n_ctx=self._config.embedding_n_ctx,
            n_threads=self._config.embedding_n_threads,
            n_batch=self._config.embedding_n_batch,
        )
        self._vector_manager = VectorStoreManager(
            persist_directory=self._config.chroma_db_path,
            collection_name=self._config.collection_name,
            embedding_service=self._embedding_service,
        )

    def check_db_exists(self) -> bool:
        """Check if ChromaDB already exists.

        Returns:
            True if database exists, False otherwise.
        """
        return self._vector_manager.check_exists()

    def run_ingestion(self, overwrite: bool = False) -> int:
        """Run ingestion pipeline.

        Args:
            overwrite: If True, overwrite existing database without prompting.

        Returns:
            Number of chunks ingested. Returns 0 if aborted.
        """
        if self._vector_manager.check_exists() and not overwrite:
            response = input("Database exists. Overwrite? (y/n): ")
            if response.lower() != "y":
                print("Aborted.")
                return 0

        input_path = Path(self._config.input_dir)
        texts = []
        metadatas = []
        for filepath, content in load_documents(input_path):
            texts.append(content)
            metadatas.append({"source": filepath})

        chunks = chunk_documents(
            texts=texts,
            chunk_size=self._config.chunk_size,
            chunk_overlap=self._config.chunk_overlap,
        )

        self._vector_manager.create_vector_store(
            documents=["Represent this sentence for searching relevant passages:"+chunk["content"] for chunk in chunks],
            metadatas=[chunk["metadata"] for chunk in chunks],
        )

        return len(chunks)

    def get_retriever(self):
        """Get vector store as retriever."""
        return self._vector_manager.as_retriever(
            {"k": self._config.top_k}
        )


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    pipeline = RAGPipeline()
    if pipeline.check_db_exists():
        response = input("Database exists. Overwrite? (y/n): ")
        overwrite = response.lower() == "y"
    else:
        overwrite = True

    if overwrite:
        chunk_count = pipeline.run_ingestion(overwrite=overwrite)
        print(f"Ingested {chunk_count} chunks")
