"""Embedding service using llama-cpp-python."""

from langchain_community.embeddings import LlamaCppEmbeddings


class EmbeddingService:
    """Wrapper for llama-cpp-python embeddings with lazy initialization."""

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 8192,
        n_threads: int = 4,
        n_batch: int = 512,
    ) -> None:
        """Initialize embedding service.

        Args:
            model_path: Path to GGUF embedding model file.
            n_ctx: Context size for embedding model.
            n_threads: Number of threads for inference.
            n_batch: Batch size for inference.
        """
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._n_threads = n_threads
        self._n_batch = n_batch
        self._embeddings: LlamaCppEmbeddings | None = None

    def get_embeddings(self) -> LlamaCppEmbeddings:
        """Get or create LlamaCppEmbeddings instance.

        Returns:
            LlamaCppEmbeddings instance.
        """
        if self._embeddings is None:
            self._embeddings = LlamaCppEmbeddings(
                model_path=self._model_path,
                n_ctx=self._n_ctx,
                n_threads=self._n_threads,
                n_batch=self._n_batch,
            )
        return self._embeddings
