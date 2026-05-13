"""Text chunking for documents."""

from typing import Any

from langchain_text_splitters import MarkdownTextSplitter, RecursiveCharacterTextSplitter


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
    splitter = MarkdownTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.create_documents(texts)
    return [{"content": chunk.page_content, "metadata": chunk.metadata} for chunk in chunks]


def chunk_documents_by_line_then_overlap(
    texts: list[str],
    line_separator: str = "\n",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[dict[str, Any]]:
    """Split text by lines first, then apply overlapping chunking to each line.

    Two-stage chunking:
    1. Split each text by line separator into individual line chunks (no overlap)
    2. For each line chunk, apply overlapping chunking with RecursiveCharacterTextSplitter

    Args:
        texts: List of text strings to chunk.
        line_separator: Separator to split text into lines (default: newline).
        chunk_size: Maximum characters per overlap chunk (applied in stage 2).
        chunk_overlap: Number of overlapping characters between overlap chunks.

    Returns:
        List of chunk dictionaries with 'content' and 'metadata' keys.
    """
    all_chunks: list[dict[str, Any]] = []

    for text in texts:
        # Stage 1: Split by line separator
        lines = text.split(line_separator)

        for line in lines:
            if not line.strip():
                continue

            # Stage 2: Apply overlapping chunking to each line
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            line_docs = splitter.create_documents([line])

            for doc in line_docs:
                chunk_dict = {
                    "content": doc.page_content,
                    "metadata": {"source": ""},
                }
                all_chunks.append(chunk_dict)

    return all_chunks
