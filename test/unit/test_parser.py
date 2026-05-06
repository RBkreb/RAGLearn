"""Unit tests for src.indexing.parser module."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.indexing.parser import Document, DocumentParser
from src.exceptions import DocumentParseError


class TestDocumentNamedTuple:
    """Tests for Document NamedTuple fields."""

    def test_document_has_content_field(self) -> None:
        """Document should have content field of type str."""
        doc = Document(content="test content", source="test.md")
        assert hasattr(doc, "content")
        assert isinstance(doc.content, str)
        assert doc.content == "test content"

    def test_document_has_source_field(self) -> None:
        """Document should have source field of type str."""
        doc = Document(content="test content", source="test.md")
        assert hasattr(doc, "source")
        assert isinstance(doc.source, str)
        assert doc.source == "test.md"

    def test_document_has_metadata_field(self) -> None:
        """Document should have metadata field of type dict or None."""
        doc = Document(content="test content", source="test.md")
        assert hasattr(doc, "metadata")
        assert doc.metadata is None

    def test_document_with_metadata(self) -> None:
        """Document should accept metadata dict."""
        metadata = {"extension": ".md", "filename": "test.md"}
        doc = Document(content="test content", source="test.md", metadata=metadata)
        assert doc.metadata == metadata

    def test_document_is_namedtuple(self) -> None:
        """Document should be a NamedTuple instance (subclass of tuple)."""
        assert issubclass(Document, tuple)
        assert hasattr(Document, "_fields")


class TestDocumentParserSupportedExtensions:
    """Tests for DocumentParser.supported_extensions class attribute."""

    def test_supported_extensions_exists(self) -> None:
        """DocumentParser should have supported_extensions attribute."""
        assert hasattr(DocumentParser, "supported_extensions")

    def test_supported_extensions_is_tuple(self) -> None:
        """supported_extensions should be a tuple."""
        assert isinstance(DocumentParser.supported_extensions, tuple)

    def test_supported_extensions_contains_markdown(self) -> None:
        """supported_extensions should contain .md extension."""
        assert ".md" in DocumentParser.supported_extensions

    def test_supported_extensions_contains_txt(self) -> None:
        """supported_extensions should contain .txt extension."""
        assert ".txt" in DocumentParser.supported_extensions

    def test_supported_extensions_contains_image_extensions(self) -> None:
        """supported_extensions should contain image extensions."""
        assert ".png" in DocumentParser.supported_extensions
        assert ".jpg" in DocumentParser.supported_extensions
        assert ".jpeg" in DocumentParser.supported_extensions


class TestDocumentParserParseMarkdown:
    """Tests for DocumentParser.parse_markdown method."""

    def test_parse_markdown_returns_document(self, tmp_path: Path) -> None:
        """parse_markdown should return a Document instance."""
        parser = DocumentParser()
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Content", encoding="utf-8")

        result = parser.parse_markdown(str(test_file))

        assert isinstance(result, Document)
        assert result.content == "# Test Content"
        assert result.source == str(test_file.absolute())

    def test_parse_markdown_extracts_metadata(self, tmp_path: Path) -> None:
        """parse_markdown should extract extension and filename as metadata."""
        parser = DocumentParser()
        test_file = tmp_path / "example.txt"
        test_file.write_text("Some text content", encoding="utf-8")

        result = parser.parse_markdown(str(test_file))

        assert result.metadata is not None
        assert result.metadata["extension"] == ".txt"
        assert result.metadata["filename"] == "example.txt"

    def test_parse_markdown_raises_error_for_missing_file(self) -> None:
        """parse_markdown should raise DocumentParseError for missing file."""
        parser = DocumentParser()

        with pytest.raises(DocumentParseError) as exc_info:
            parser.parse_markdown("/nonexistent/path/file.md")

        assert "File not found" in str(exc_info.value.message)
        assert exc_info.value.source == "/nonexistent/path/file.md"


class TestDocumentParserParseDirectory:
    """Tests for DocumentParser.parse_directory method."""

    def test_parse_directory_returns_list(self, tmp_path: Path) -> None:
        """parse_directory should return a list of Documents."""
        parser = DocumentParser()
        (tmp_path / "doc1.md").write_text("Content 1", encoding="utf-8")
        (tmp_path / "doc2.md").write_text("Content 2", encoding="utf-8")

        result = parser.parse_directory(str(tmp_path))

        assert isinstance(result, list)
        assert len(result) == 2

    def test_parse_directory_contains_document_instances(self, tmp_path: Path) -> None:
        """parse_directory should return Document instances."""
        parser = DocumentParser()
        (tmp_path / "test.md").write_text("Test content", encoding="utf-8")

        result = parser.parse_directory(str(tmp_path))

        for doc in result:
            assert isinstance(doc, Document)

    def test_parse_directory_raises_error_for_invalid_directory(self) -> None:
        """parse_directory should raise DocumentParseError for invalid directory."""
        parser = DocumentParser()

        with pytest.raises(DocumentParseError) as exc_info:
            parser.parse_directory("/nonexistent/invalid/directory")

        assert "Invalid directory" in str(exc_info.value.message)


class TestDocumentParserImport:
    """Tests for module imports."""

    def test_document_can_be_imported_from_module(self) -> None:
        """Document should be importable from src.indexing.parser."""
        from src.indexing.parser import Document
        assert Document is not None

    def test_documentparser_can_be_imported_from_module(self) -> None:
        """DocumentParser should be importable from src.indexing.parser."""
        from src.indexing.parser import DocumentParser
        assert DocumentParser is not None
