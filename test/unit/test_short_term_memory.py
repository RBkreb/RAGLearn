"""Tests for short_term_memory module."""

import tempfile
from pathlib import Path

import pytest

from src.short_term_memory import ShortTermMemory


class TestShortTermMemory:
    """Tests for ShortTermMemory class."""

    def test_add_user_message(self) -> None:
        """Test adding user message."""
        memory = ShortTermMemory(session_id="test_session")
        memory.add_user_message("Hello")
        messages = memory.get_messages()
        assert len(messages) == 1
        assert messages[0].content == "Hello"

    def test_add_ai_message(self) -> None:
        """Test adding AI message."""
        memory = ShortTermMemory(session_id="test_session")
        memory.add_ai_message("Hi there")
        messages = memory.get_messages()
        assert len(messages) == 1
        assert messages[0].content == "Hi there"

    def test_get_last_user_message(self) -> None:
        """Test getting last user message."""
        memory = ShortTermMemory(session_id="test_session")
        memory.add_user_message("First")
        memory.add_ai_message("Second")
        memory.add_user_message("Third")
        assert memory.get_last_user_message() == "Third"

    def test_get_last_ai_message(self) -> None:
        """Test getting last AI message."""
        memory = ShortTermMemory(session_id="test_session")
        memory.add_user_message("First")
        memory.add_ai_message("Second")
        memory.add_user_message("Third")
        memory.add_ai_message("Fourth")
        assert memory.get_last_ai_message() == "Fourth"

    def test_rewind(self) -> None:
        """Test rewinding conversation."""
        memory = ShortTermMemory(session_id="test_session")
        memory.add_user_message("User1")
        memory.add_ai_message("AI1")
        memory.add_user_message("User2")
        memory.add_ai_message("AI2")
        memory.rewind(1)
        assert len(memory.messages) == 2
        assert memory.get_last_user_message() == "User1"

    def test_compact(self) -> None:
        """Test compacting memory with summary."""
        memory = ShortTermMemory(session_id="test_session")
        memory.add_user_message("Long conversation")
        memory.add_ai_message("More content")
        memory.compact("Summary of conversation")
        messages = memory.get_messages()
        assert len(messages) == 1
        assert "Summary" in messages[0].content

    def test_save_and_load(self) -> None:
        """Test saving and loading memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = ShortTermMemory(session_id="test_session")
            memory.add_user_message("User message")
            memory.add_ai_message("AI response")

            path = Path(tmpdir) / "test.json"
            memory.save(path)

            loaded = ShortTermMemory.load(path)
            assert len(loaded.messages) == 2
            assert loaded.session_id == "test_session"

    def test_token_count(self) -> None:
        """Test token count estimation."""
        memory = ShortTermMemory(session_id="test_session")
        memory.add_user_message("Hello world")
        assert memory.token_count > 0

    def test_message_count(self) -> None:
        """Test message count."""
        memory = ShortTermMemory(session_id="test_session")
        memory.add_user_message("First")
        memory.add_user_message("Second")
        assert memory.message_count() == 2