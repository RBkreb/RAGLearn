"""JSONL document splitter with hash metadata."""

import json
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import IndexConfig
from src.utils.hash import compute_hash


class JsonlSplitter:
    """Split JSONL documents using RecursiveCharacterTextSplitter.

    Each JSONL line is a pre-chunked document entry. The text field
    from each entry is further split using the same RecursiveCharacterTextSplitter
    strategy as LineSplitter — no line-based pre-splitting here because
    JSONL entries are already individual chunks.
    """

    def __init__(
        self,
        text_field: str = "context",
        separators: list[str] | None = None,
    ) -> None:
        """Initialize the JsonlSplitter.

        Args:
            text_field: JSON field name for the text content.
            separators: Custom separators for RecursiveCharacterTextSplitter.
        """
        self.config = IndexConfig()
        self._text_field = text_field
        if separators is None:
            separators = ["\n\n", "\n", "。", "！", "？", "，", " ", ""]

        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=separators,
            length_function=len,
        )

    def _load_entries(self, directory: str) -> list[dict]:
        """Load all JSONL files from a directory, parsing each line as a JSON entry."""
        entries: list[dict] = []
        dir_path = Path(directory)
        for file_path in dir_path.rglob("*.jsonl"):
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return entries

    def split_directory(self, directory: str = "./inputs") -> list[Document]:
        """Load JSONL files and split each entry's text field into chunks.

        Args:
            directory: Path to the directory containing .jsonl files.

        Returns:
            List of Document objects with hash metadata.
        """
        entries = self._load_entries(directory)
        results: list[Document] = []

        for entry_idx, entry in enumerate(entries):
            content = entry.get(self._text_field, "")
            if not content:
                continue
            title = entry.get("title", str(entry.get("doc_id", entry_idx)))
            sub_chunks = self._text_splitter.split_text(content)
            for sub_idx, sub_chunk in enumerate(sub_chunks):
                chunk_hash = compute_hash(sub_chunk)
                metadata = {
                    "source": title,
                    "entry_index": entry_idx,
                    "sub_chunk_index": sub_idx,
                    "hash": chunk_hash,
                    "doc_id": entry.get("doc_id", ""),
                }
                results.append(Document(
                    page_content=sub_chunk,
                    metadata=metadata
                ))

        return results
