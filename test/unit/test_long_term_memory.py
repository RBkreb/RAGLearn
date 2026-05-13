"""Tests for long_term_memory module."""

import tempfile
from pathlib import Path

import pytest

from src.long_term_memory import LongTermMemory, MemoryEntry, SessionMemory


class TestMemoryEntry:
    """Tests for MemoryEntry dataclass."""

    def test_creation(self) -> None:
        """Test creating a MemoryEntry."""
        entry = MemoryEntry(
            timestamp="2024-01-01T00:00:00",
            content="test content",
            tags=["test"],
            session_id="session123",
        )
        assert entry.content == "test content"
        assert entry.tags == ["test"]


class TestSessionMemory:
    """Tests for SessionMemory class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self._session = SessionMemory(session_id="test_session")

    def test_add_summary(self) -> None:
        """Test adding summary."""
        self._session.add_summary("Test summary", ["tag1"])
        assert len(self._session.summaries) == 1
        assert self._session.summaries[0].content == "Test summary"

    def test_add_key_info(self) -> None:
        """Test adding key information."""
        self._session.add_key_info("Important info")
        assert len(self._session.key_info) == 1

    def test_search(self) -> None:
        """Test searching memory entries."""
        self._session.add_summary("Python is great", ["python", "programming"])
        results = self._session.search("python")
        assert len(results) == 1
        assert "Python" in results[0]

    def test_search_no_match(self) -> None:
        """Test search with no matches."""
        results = self._session.search("nonexistent")
        assert len(results) == 0

    def test_to_system_message(self) -> None:
        """Test converting to system message."""
        self._session.add_summary("Test summary")
        msg = self._session.to_system_message()
        assert len(msg.content) > 0


class TestLongTermMemory:
    """Tests for LongTermMemory class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self._tmpdir = tempfile.mkdtemp()
        self._storage_dir = Path(self._tmpdir)
        self._memory = LongTermMemory(self._storage_dir)

    def test_create_session(self) -> None:
        """Test creating a session memory."""
        session = self._memory.create_session("session123")
        assert session is not None
        assert session.session_id == "session123"

    def test_get_session(self) -> None:
        """Test getting session memory."""
        self._memory.create_session("session123")
        session = self._memory.get_session("session123")
        assert session is not None

    def test_get_nonexistent_session(self) -> None:
        """Test getting non-existent session returns None."""
        result = self._memory.get_session("nonexistent")
        assert result is None

    def test_add_summary(self) -> None:
        """Test adding summary to session."""
        self._memory.add_summary("session123", "Test summary", ["tag1"])
        session = self._memory.get_session("session123")
        assert session is not None
        assert len(session.summaries) == 1

    def test_add_key_info(self) -> None:
        """Test adding key info to session."""
        self._memory.add_key_info("session123", "Key info")
        session = self._memory.get_session("session123")
        assert session is not None
        assert len(session.key_info) == 1

    def test_search_session(self) -> None:
        """Test searching within a session."""
        self._memory.add_summary("session123", "Python tutorial")
        results = self._memory.search_session("session123", "Python")
        assert len(results) == 1

    def test_get_context(self) -> None:
        """Test getting context as system message."""
        self._memory.create_session("session123")
        msg = self._memory.get_context("session123")
        assert msg.content is not None