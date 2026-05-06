"""LLM wrapper for LangChain LlamaCpp chat model."""

from langchain_community.chat_models import ChatLlamaCpp

from src.config import LlamaCppConfig
from src.exceptions import EmbeddingError


class LlamaCppLLMWrapper:
    """Wrapper for LangChain ChatLlamaCpp (Qwen3.5 GGUF).

    This class wraps langchain_community.chat_models.ChatLlamaCpp to provide
    a consistent interface for the RAG pipeline.

    Attributes:
        config: LlamaCpp configuration dataclass.
        _model: The underlying ChatLlamaCpp instance.
    """

    def __init__(self, config: LlamaCppConfig) -> None:
        """Initialize LlamaCpp LLM wrapper.

        Args:
            config: LlamaCpp configuration including model path and parameters.
        """
        self.config = config
        self._model = ChatLlamaCpp(
            model_path=config.model_path,
            temperature=config.temperature,
            n_ctx=config.n_ctx,
            n_gpu_layers=config.n_gpu_layers,
            verbose=False,
            max_tokens=config.max_tokens,
        )

    def _sanitize_text(self, text: str) -> str:
        """Remove surrogate characters that cannot be encoded to UTF-8.

        Args:
            text: Input text string.

        Returns:
            Text with surrogate characters removed.
        """
        return text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

    def invoke(self, prompt: str) -> str:
        """Invoke the LLM with a prompt.

        Args:
            prompt: The input prompt string.

        Returns:
            The LLM's text response.

        Raises:
            EmbeddingError: If the LLM invocation fails.
        """
        try:
            clean_prompt = self._sanitize_text(prompt)
            response = self._model.invoke(clean_prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            raise EmbeddingError(f"LLM invocation failed: {e}") from e

    def generate(self, prompts: list[str]) -> list[str]:
        """Generate responses for multiple prompts.

        Args:
            prompts: List of input prompt strings.

        Returns:
            List of LLM text responses.

        Raises:
            EmbeddingError: If any LLM invocation fails.
        """
        try:
            clean_prompts = [self._sanitize_text(p) for p in prompts]
            responses = self._model.batch(clean_prompts)
            return [
                r.content if hasattr(r, "content") else str(r) for r in responses
            ]
        except Exception as e:
            raise EmbeddingError(f"Batch LLM invocation failed: {e}") from e


def create_llm(config: LlamaCppConfig | None = None) -> LlamaCppLLMWrapper:
    """Factory function to create a LlamaCppLLMWrapper.

    Args:
        config: Optional LlamaCpp configuration. Uses defaults if not provided.

    Returns:
        Configured LlamaCppLLMWrapper instance.
    """
    if config is None:
        config = LlamaCppConfig()
    return LlamaCppLLMWrapper(config)
