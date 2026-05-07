"""Unit tests for document loader."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline.document_loader import load_documents


class TestLoadDocuments:
    """Tests for load_documents function."""

    def test_load_documents_raises_error_for_invalid_directory(self) -> None:
        """Should raise ValueError when input directory does not exist."""
        invalid_path = Path("nonexistent_directory")

        with pytest.raises(ValueError, match="Input directory does not exist"):
            list(load_documents(invalid_path))

    def test_load_documents_returns_empty_for_directory_with_no_markdown_or_text(
        self, tmp_path: Path
    ) -> None:
        """Should return empty iterator when directory has no .md or .txt files."""
        result = list(load_documents(tmp_path))

        assert result == []

    @patch("src.pipeline.document_loader.Path.read_text")
    def test_load_documents_loads_markdown_files(
        self, mock_read_text: MagicMock, tmp_path: Path
    ) -> None:
        """Should load and yield content from .md files."""
        mock_read_text.return_value = "# Test Document\n\nSome content."

        md_file = tmp_path / "test.md"
        md_file.touch()

        with patch.object(Path, "iterdir", return_value=[md_file]):
            result = list(load_documents(tmp_path))

        assert len(result) == 1
        filepath, content = result[0]
        assert "test.md" in filepath
        assert "# Test Document" in content

    @patch("src.pipeline.document_loader.Path.read_text")
    def test_load_documents_loads_text_files(
        self, mock_read_text: MagicMock, tmp_path: Path
    ) -> None:
        """Should load and yield content from .txt files."""
        mock_read_text.return_value = "Plain text content."

        txt_file = tmp_path / "document.txt"
        txt_file.touch()

        with patch.object(Path, "iterdir", return_value=[txt_file]):
            result = list(load_documents(tmp_path))

        assert len(result) == 1
        filepath, content = result[0]
        assert "document.txt" in filepath
        assert "Plain text content." in content

    @patch("src.pipeline.document_loader.Path.read_text")
    def test_load_documents_filters_by_extension_case_insensitive(
        self, mock_read_text: MagicMock, tmp_path: Path
    ) -> None:
        """Should load files with .MD and .TXT extensions (case insensitive)."""
        mock_read_text.return_value = "content"

        md_file_upper = tmp_path / "test.MD"
        txt_file_upper = tmp_path / "test.TXT"
        md_file_upper.touch()
        txt_file_upper.touch()

        with patch.object(Path, "iterdir", return_value=[md_file_upper, txt_file_upper]):
            result = list(load_documents(tmp_path))

        assert len(result) == 2

    @patch("src.pipeline.document_loader.Path.read_text")
    def test_load_documents_skips_other_file_types(
        self, mock_read_text: MagicMock, tmp_path: Path
    ) -> None:
        """Should skip files that are not .md or .txt."""
        mock_read_text.return_value = "content"

        md_file = tmp_path / "test.md"
        pdf_file = tmp_path / "test.pdf"
        py_file = tmp_path / "test.py"
        md_file.touch()
        pdf_file.touch()
        py_file.touch()

        with patch.object(Path, "iterdir", return_value=[md_file, pdf_file, py_file]):
            result = list(load_documents(tmp_path))

        assert len(result) == 1
        assert "test.md" in result[0][0]

    @patch("src.pipeline.document_loader.Path.read_text")
    def test_load_documents_yields_tuple_of_filepath_and_content(
        self, mock_read_text: MagicMock, tmp_path: Path
    ) -> None:
        """Should yield tuples of (filepath string, content string)."""
        expected_content = "Test content"
        mock_read_text.return_value = expected_content

        md_file = tmp_path / "test.md"
        md_file.touch()

        with patch.object(Path, "iterdir", return_value=[md_file]):
            result = list(load_documents(tmp_path))

        assert len(result) == 1
        filepath, content = result[0]
        assert isinstance(filepath, str)
        assert isinstance(content, str)
        assert content == expected_content

    @patch("src.pipeline.document_loader.Path.read_text")
    def test_load_documents_reads_with_utf8_encoding(
        self, mock_read_text: MagicMock, tmp_path: Path
    ) -> None:
        """Should read files with UTF-8 encoding."""
        md_file = tmp_path / "test.md"
        md_file.touch()

        with patch.object(Path, "iterdir", return_value=[md_file]):
            list(load_documents(tmp_path))

        mock_read_text.assert_called_once_with(encoding="utf-8")
