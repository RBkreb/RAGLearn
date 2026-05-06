"""Custom exception hierarchy for RAG Q&A bot."""


class RAGError(Exception):
    """Base exception for all RAG-related errors.

    This is the parent class for all specific exceptions in the RAG system.
    """

    def __init__(self, message: str) -> None:
        """Initialize RAGError with message.

        Args:
            message: Error description.
        """
        super().__init__(message)
        self.message = message


class DocumentParseError(RAGError):
    """Raised when document parsing fails."""

    def __init__(self, message: str, source: str | None = None) -> None:
        """Initialize DocumentParseError.

        Args:
            message: Error description.
            source: Optional path to the document that failed to parse.
        """
        super().__init__(message)
        self.source = source


class ChunkingError(RAGError):
    """Raised when text chunking fails."""


class EmbeddingError(RAGError):
    """Raised when embedding generation fails."""


class IndexError(RAGError):
    """Raised when vector index operations fail."""


class RetrievalError(RAGError):
    """Raised when retrieval operations fail."""


class ConfigurationError(RAGError):
    """Raised when configuration is invalid or missing."""


class PipelineError(RAGError):
    """Raised when pipeline operations fail."""