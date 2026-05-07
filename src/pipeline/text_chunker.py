"""Text chunking for documents."""

from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_documents(
    texts: list[str],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[dict[str, Any]]:
    """Split documents into overlapping chunks.

    Args:
        texts: List of text strings to chunk.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List of chunk dictionaries with 'content' and 'metadata' keys.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.create_documents(texts)
    return [{"content": chunk.page_content, "metadata": chunk.metadata} for chunk in chunks]
