"""Line-based document splitter with hash metadata."""

from dataclasses import dataclass
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.utils.hash import compute_hash
from src.config import IndexConfig

class LineSplitter:
    """Split documents by line, then apply RecursiveCharacterTextSplitter.

    Each line is treated as an initial chunk. Then each line chunk is further
    split using LangChain's RecursiveCharacterTextSplitter. The hash of each
    final chunk is computed and stored in its metadata.
    """

    def __init__(
        self,
        separators: list[str] | None = None,
    ) -> None:
        """Initialize the LineSplitter.

        Args:
            chunk_size: Maximum size of each final chunk (in characters).
            chunk_overlap: Overlap between consecutive chunks.
            separators: Custom separators for RecursiveCharacterTextSplitter.
        """
        self.config=IndexConfig()
        if separators is None:
            separators = ["\n\n", "\n", "。", "！", "？", "，", " ", ""]

        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=separators,
            length_function=len,
        )

    def split_file(self, file_path: str) -> list[Document]:
        """Read a file and split it into chunks.

        Args:
            file_path: Path to the input file.

        Returns:
            List of ChunkResult objects with content, hash, and metadata.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        results: list[Document] = []

        for line_idx, line in enumerate(lines):
            if not line.strip():
                continue

            sub_chunks = self._text_splitter.split_text(line)

            for sub_idx, sub_chunk in enumerate(sub_chunks):
                chunk_hash = compute_hash(sub_chunk)
                metadata = {
                    "source":file_path,
                    "line_index": line_idx,
                    "sub_chunk_index": sub_idx,
                    "hash": chunk_hash,
                }
                results.append(Document(
                    page_content=sub_chunk,
                    metadata=metadata
                ))

        return results