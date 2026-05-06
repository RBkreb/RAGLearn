"""Embedding wrapper for llama-cpp-python embedding model."""

from llama_cpp import Llama

from src.config import LlamaCppConfig
from src.exceptions import EmbeddingError


class LlamaCppEmbeddingWrapper:
    """Wrapper for llama-cpp-python embedding model (Qwen3-Embedding GGUF).

    This class wraps llama_cpp.Llama with embedding=True to provide a consistent
    interface for the RAG pipeline.

    Attributes:
        config: LlamaCpp configuration dataclass.
        _model: The underlying Llama instance with embedding mode.
    """

    def __init__(self, config: LlamaCppConfig) -> None:
        """Initialize LlamaCpp embedding wrapper.

        Args:
            config: LlamaCpp configuration including model path and parameters.
        """
        self.config = config
        self._model = Llama(
            model_path=config.embedding_model_path,
            embedding=True,
            n_gpu_layers=config.n_gpu_layers,
            verbose=False,
        )

    def _sanitize_text(self, text: str) -> str:
        """Remove surrogate characters that cannot be encoded to UTF-8.

        Args:
            text: Input text string.

        Returns:
            Text with surrogate characters removed.
        """
        return text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Input text string.

        Returns:
            List of embedding values.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        try:
            clean_text = self._sanitize_text(text)
            return self._model.embed(clean_text)
        except Exception as e:
            raise EmbeddingError(f"Embedding generation failed: {e}") from e

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input text strings.

        Returns:
            List of embedding lists.

        Raises:
            EmbeddingError: If any embedding generation fails.
        """
        try:
            clean_texts = [self._sanitize_text(t) for t in texts]
            return [self._model.embed(text) for text in clean_texts]
        except Exception as e:
            raise EmbeddingError(f"Batch embedding generation failed: {e}") from e


def create_embedding(config: LlamaCppConfig | None = None) -> LlamaCppEmbeddingWrapper:
    """Factory function to create a LlamaCppEmbeddingWrapper.

    Args:
        config: Optional LlamaCpp configuration. Uses defaults if not provided.

    Returns:
        Configured LlamaCppEmbeddingWrapper instance.
    """
    if config is None:
        config = LlamaCppConfig()
    return LlamaCppEmbeddingWrapper(config)
