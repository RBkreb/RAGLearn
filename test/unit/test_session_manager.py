"""Tests for session_manager module."""

import json
import tempfile
from pathlib import Path

import pytest

from src.session_manager import Session, SessionManager


class TestSessionManager:
    """Tests for SessionManager class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self._tmpdir = tempfile.mkdtemp()
        self._storage_dir = Path(self._tmpdir)
        self._manager = SessionManager(self._storage_dir)

    def test_create_session(self) -> None:
        """Test creating a new session."""
        session = self._manager.create_session("test")
        assert session.name == "test"
        assert session.session_id is not None
        assert self._manager.current_session_id == session.session_id

    def test_create_session_without_name(self) -> None:
        """Test creating session without name."""
        session = self._manager.create_session()
        assert session.name == session.session_id

    def test_get_session(self) -> None:
        """Test getting a session by ID."""
        created = self._manager.create_session("test")
        retrieved = self._manager.get_session(created.session_id)
        assert retrieved is not None
        assert retrieved.session_id == created.session_id

    def test_get_nonexistent_session(self) -> None:
        """Test getting non-existent session returns None."""
        result = self._manager.get_session("nonexistent")
        assert result is None

    def test_delete_session(self) -> None:
        """Test deleting a session."""
        session = self._manager.create_session("test")
        result = self._manager.delete_session(session.session_id)
        assert result is True
        assert self._manager.get_session(session.session_id) is None

    def test_delete_nonexistent_session(self) -> None:
        """Test deleting non-existent session returns False."""
        result = self._manager.delete_session("nonexistent")
        assert result is False

    def test_switch_session(self) -> None:
        """Test switching to different session."""
        session1 = self._manager.create_session("first")
        session2 = self._manager.create_session("second")
        result = self._manager.switch_session(session1.session_id)
        assert result is True
        assert self._manager.current_session_id == session1.session_id

    def test_switch_to_nonexistent_session(self) -> None:
        """Test switching to non-existent session returns False."""
        result = self._manager.switch_session("nonexistent")
        assert result is False

    def test_switch_session_by_name(self) -> None:
        """Test switching to session by name."""
        session = self._manager.create_session("my_session")
        result = self._manager.switch_session("my_session")
        assert result is True
        assert self._manager.current_session_id == session.session_id

    def test_list_sessions(self) -> None:
        """Test listing all sessions."""
        import time
        session1 = self._manager.create_session("first")
        time.sleep(1.1)
        session2 = self._manager.create_session("second")
        sessions = self._manager.list_sessions()
        assert len(sessions) >= 2

    def test_save_and_load_memory(self) -> None:
        """Test saving and loading memory."""
        from src.short_term_memory import ShortTermMemory

        session = self._manager.create_session("test")
        memory = ShortTermMemory(session_id=session.session_id)
        memory.add_user_message("test message")

        self._manager.save_memory(memory)
        loaded = self._manager.load_memory(session.session_id)

        assert loaded is not None
        assert loaded.session_id == session.session_id

    def test_load_memory_nonexistent_session(self) -> None:
        """Test loading memory for non-existent session returns None."""
        result = self._manager.load_memory("nonexistent")
        assert result is None


class TestSession:
    """Tests for Session dataclass."""

    def test_session_creation(self) -> None:
        """Test creating a Session object."""
        session = Session(
            session_id="test123",
            name="Test Session",
            created_at="2024-01-01T00:00:00",
            last_active="2024-01-01T00:00:00",
        )
        assert session.session_id == "test123"
        assert session.name == "Test Session"