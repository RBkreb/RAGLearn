"""Text chunking module with overlap support."""

from typing import NamedTuple

from src.indexing.parser import Document


class Chunk(NamedTuple):
    """Immutable chunk container.

    Attributes:
        content: The text content of the chunk.
        source: Path or identifier for the document source.
        chunk_index: Index of this chunk within the document.
        total_chunks: Total number of chunks from this document.
    """

    content: str
    source: str
    chunk_index: int
    total_chunks: int
    metadata: dict[str, str] | None = None


class TextChunker:
    """Text chunker with configurable size and overlap.

    This class handles splitting documents into overlapping chunks
    for embedding and retrieval.

    Attributes:
        chunk_size: Target size for each chunk in characters.
        chunk_overlap: Number of overlapping characters between chunks.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        """Initialize TextChunker.

        Args:
            chunk_size: Target size for each chunk in characters.
            chunk_overlap: Number of overlapping characters between chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_documents(self, documents: list[Document]) -> list[Chunk]:
        """Chunk multiple documents.

        Args:
            documents: List of documents to chunk.

        Returns:
            List of all chunks from all documents.
        """
        chunks: list[Chunk] = []
        for doc in documents:
            doc_chunks = self.chunk_text(doc.content, doc.source, doc.metadata)
            chunks.extend(doc_chunks)
        return chunks

    def chunk_text(
        self, text: str, source: str, metadata: dict[str, str] | None = None
    ) -> list[Chunk]:
        """Split text into overlapping chunks.

        Args:
            text: Input text to chunk.
            source: Source identifier for the text.
            metadata: Optional metadata to attach to chunks.

        Returns:
            List of Chunk namedtuples.
        """
        if not text:
            return []

        chunks: list[Chunk] = []
        start = 0
        text_length = len(text)
        chunk_index = 0

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunk_content = text[start:end]

            chunks.append(
                Chunk(
                    content=chunk_content,
                    source=source,
                    chunk_index=chunk_index,
                    total_chunks=0,
                    metadata=metadata,
                )
            )

            chunk_index += 1
            start += self.chunk_size - self.chunk_overlap

        total = len(chunks)
        result: list[Chunk] = []
        for c in chunks:
            result.append(
                Chunk(
                    content=c.content,
                    source=c.source,
                    chunk_index=c.chunk_index,
                    total_chunks=total,
                    metadata=c.metadata,
                )
            )

        return result