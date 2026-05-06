"""Document parser for markdown and image files."""

import os
from pathlib import Path
from typing import NamedTuple


class Document(NamedTuple):
    """Immutable document container.

    Attributes:
        content: The text content of the document.
        source: Path or identifier for the document source.
        metadata: Additional metadata about the document.
    """

    content: str
    source: str
    metadata: dict[str, str] | None = None


class DocumentParser:
    """Parser for markdown and image documents.

    This class handles parsing of documents from the filesystem,
    supporting markdown files and basic image file handling.

    Attributes:
        supported_extensions: File extensions supported for parsing.
    """

    supported_extensions: tuple[str, ...] = (".md", ".txt", ".png", ".jpg", ".jpeg")

    def parse_markdown(self, file_path: str) -> Document:
        """Parse a markdown file.

        Args:
            file_path: Path to the markdown file.

        Returns:
            Document with content and source.

        Raises:
            DocumentParseError: If file cannot be read.
        """
        from src.exceptions import DocumentParseError

        try:
            path = Path(file_path)
            if not path.exists():
                raise DocumentParseError(
                    f"File not found: {file_path}", source=file_path
                )

            content = path.read_text(encoding="utf-8")
            return Document(
                content=content,
                source=str(path.absolute()),
                metadata={"extension": path.suffix, "filename": path.name},
            )
        except DocumentParseError:
            raise
        except Exception as e:
            raise DocumentParseError(f"Failed to parse markdown: {e}", source=file_path) from e

    def parse_directory(self, directory: str) -> list[Document]:
        """Parse all supported documents in a directory.

        Args:
            directory: Path to the directory.

        Returns:
            List of parsed documents.

        Raises:
            DocumentParseError: If directory cannot be accessed.
        """
        from src.exceptions import DocumentParseError

        docs: list[Document] = []
        try:
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                raise DocumentParseError(f"Invalid directory: {directory}")

            for file_path in path.rglob("*"):
                if file_path.suffix.lower() in self.supported_extensions:
                    if file_path.suffix.lower() in (".md", ".txt"):
                        docs.append(self.parse_markdown(str(file_path)))
                    else:
                        docs.append(self._parse_image(str(file_path)))

            return docs
        except DocumentParseError:
            raise
        except Exception as e:
            raise DocumentParseError(f"Failed to parse directory: {e}") from e

    def _parse_image(self, file_path: str) -> Document:
        """Parse an image file placeholder.

        Args:
            file_path: Path to the image file.

        Returns:
            Document with placeholder content.
        """
        path = Path(file_path)
        return Document(
            content=f"[Image: {path.name}]",
            source=str(path.absolute()),
            metadata={"extension": path.suffix, "filename": path.name, "type": "image"},
        )