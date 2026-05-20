"""Line-based document splitter with hash metadata."""

from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import IndexConfig
from src.utils.hash import compute_hash


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
            separators: Custom separators for RecursiveCharacterTextSplitter.
        """
        self.config = IndexConfig()
        if separators is None:
            separators = ["\n\n", "\n", "。", "！", "？", "，", " ", ""]

        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=separators,
            length_function=len,
        )

    def _load_documents(self, directory: str) -> list[Document]:
        """Load all txt, md, and extensionless files from a directory."""
        loader = DirectoryLoader(
            directory,
            glob="**/[!.]*",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            silent_errors=True,
        )
        raw_docs = loader.load()
        return [
            doc for doc in raw_docs
            if Path(doc.metadata["source"]).suffix in ("", ".txt", ".md")
        ]

    def _split_content(self, content: str, source: str) -> list[Document]:
        """Split a single document's content into chunks with hash metadata."""
        results: list[Document] = []
        lines = content.split("\n")

        for line_idx, line in enumerate(lines):
            if not line.strip():
                continue
            sub_chunks = self._text_splitter.split_text(line)
            for sub_idx, sub_chunk in enumerate(sub_chunks):
                chunk_hash = compute_hash(sub_chunk)
                metadata = {
                    "source": source,
                    "line_index": line_idx,
                    "sub_chunk_index": sub_idx,
                    "hash": chunk_hash,
                }
                results.append(Document(
                    page_content=sub_chunk,
                    metadata=metadata
                ))

        return results

    def split_file(self, file_path: str) -> list[Document]:
        """Read a single file and split it into chunks.

        Args:
            file_path: Path to the input file.

        Returns:
            List of Document objects with hash metadata.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self._split_content(content, file_path)

    def split_directory(self, directory: str = "./inputs") -> list[Document]:
        """Load all txt, md, and extensionless files from a directory and split into chunks.

        Args:
            directory: Path to the directory containing input files.

        Returns:
            List of Document objects with hash metadata.
        """
        raw_docs = self._load_documents(directory)
        results: list[Document] = []
        for doc in raw_docs:
            source = doc.metadata.get("source", "")
            results.extend(self._split_content(doc.page_content, source))
        return results
