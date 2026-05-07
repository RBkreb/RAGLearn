"""Unit tests for memory_manager.py - MemoryManager."""

import pytest

from src.memory_manager import MemoryManager
from src.router import QueryMode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class TestMemoryManagerInit:
    """Tests for MemoryManager initialization."""

    def test_init_creates_empty_messages_list(self):
        """Test that __init__ creates empty _messages list."""
        manager = MemoryManager()
        assert manager._messages == []
        assert len(manager._messages) == 0


class TestMemoryManagerAddMessages:
    """Tests for add_user_message and add_ai_message."""

    def test_add_user_message_appends_human_message(self):
        """Test add_user_message appends HumanMessage to _messages."""
        manager = MemoryManager()
        manager.add_user_message("Hello AI")

        assert len(manager._messages) == 1
        assert isinstance(manager._messages[0], HumanMessage)
        assert manager._messages[0].content == "Hello AI"

    def test_add_ai_message_appends_ai_message(self):
        """Test add_ai_message appends AIMessage to _messages."""
        manager = MemoryManager()
        manager.add_ai_message("Hello Human")

        assert len(manager._messages) == 1
        assert isinstance(manager._messages[0], AIMessage)
        assert manager._messages[0].content == "Hello Human"

    def test_add_ai_message_ignores_tool_calls_param(self):
        """Test add_ai_message ignores tool_calls - stored separately."""
        manager = MemoryManager()
        tool_calls = [{"name": "add", "args": {"a": 1, "b": 2}}]
        manager.add_ai_message("Result is 3", tool_calls=tool_calls)

        assert len(manager._messages) == 1
        assert isinstance(manager._messages[0], AIMessage)
        # tool_calls not stored in message itself
        assert manager._messages[0].tool_calls == []


class TestMemoryManagerGetMessages:
    """Tests for get_messages method."""

    def test_get_messages_returns_messages_sequence(self):
        """Test get_messages returns the _messages list."""
        manager = MemoryManager()
        manager.add_user_message("Hello")
        manager.add_ai_message("Hi there")

        result = manager.get_messages()

        assert len(result) == 2
        assert result[0].content == "Hello"
        assert result[1].content == "Hi there"

    def test_get_messages_empty_returns_empty_sequence(self):
        """Test get_messages with empty history returns empty sequence."""
        manager = MemoryManager()
        result = manager.get_messages()

        assert len(result) == 0


class TestMemoryManagerClear:
    """Tests for clear method."""

    def test_clear_clears_messages(self):
        """Test clear removes all messages from _messages."""
        manager = MemoryManager()
        manager.add_user_message("Hello")
        manager.add_ai_message("Hi there")

        manager.clear()

        assert len(manager._messages) == 0


class TestMemoryManagerGetConversationContext:
    """Tests for get_conversation_context method."""

    def test_get_conversation_context_empty_history(self):
        """Test get_conversation_context with empty history returns empty string."""
        manager = MemoryManager()
        result = manager.get_conversation_context()

        assert result == ""

    def test_get_conversation_context_with_human_message(self):
        """Test get_conversation_context formats HumanMessage correctly."""
        manager = MemoryManager()
        manager.add_user_message("Hello")

        result = manager.get_conversation_context()

        assert result == "User: Hello"

    def test_get_conversation_context_with_ai_message(self):
        """Test get_conversation_context formats AIMessage correctly."""
        manager = MemoryManager()
        manager.add_ai_message("Hi there")

        result = manager.get_conversation_context()

        assert result == "Assistant: Hi there"

    def test_get_conversation_context_with_multiple_messages(self):
        """Test get_conversation_context with alternating messages."""
        manager = MemoryManager()
        manager.add_user_message("First question")
        manager.add_ai_message("First answer")
        manager.add_user_message("Second question")
        manager.add_ai_message("Second answer")

        result = manager.get_conversation_context()

        expected = "User: First question\nAssistant: First answer\nUser: Second question\nAssistant: Second answer"
        assert result == expected

    def test_get_conversation_context_ignores_other_message_types(self):
        """Test get_conversation_context ignores non Human/AIMessage types."""
        manager = MemoryManager()
        manager._messages.append(SystemMessage(content="System prompt"))
        manager.add_user_message("User message")
        manager.add_ai_message("AI message")

        result = manager.get_conversation_context()

        assert "System:" not in result
        assert "User: User message" in result
        assert "Assistant: AI message" in result


class TestMemoryManagerSaveContext:
    """Tests for save_context method."""

    def test_save_context_adds_both_messages(self):
        """Test save_context adds user message and AI response."""
        manager = MemoryManager()
        manager.save_context("User query", "AI response")

        assert len(manager._messages) == 2
        assert isinstance(manager._messages[0], HumanMessage)
        assert manager._messages[0].content == "User query"
        assert isinstance(manager._messages[1], AIMessage)
        assert manager._messages[1].content == "AI response"

    def test_save_context_with_tool_calls_ignored(self):
        """Test save_context ignores tool_calls - stored separately in memory."""
        manager = MemoryManager()
        tool_calls = [{"name": "add", "args": {"a": 1, "b": 2}}]
        manager.save_context("query", "response", tool_calls=tool_calls)

        assert len(manager._messages) == 2
        # tool_calls not stored in message itself


class TestMemoryManagerShouldUseMemory:
    """Tests for should_use_memory method."""

    def test_should_use_memory_base_mode(self):
        """Test should_use_memory returns True for BASE mode."""
        manager = MemoryManager()
        assert manager.should_use_memory(QueryMode.BASE) is True

    def test_should_use_memory_direct_mode(self):
        """Test should_use_memory returns False for DIRECT mode."""
        manager = MemoryManager()
        assert manager.should_use_memory(QueryMode.DIRECT) is False

    def test_should_use_memory_default_mode(self):
        """Test should_use_memory returns False for DEFAULT mode."""
        manager = MemoryManager()
        assert manager.should_use_memory(QueryMode.DEFAULT) is False


class TestMemoryManagerIntegration:
    """Integration-style tests for MemoryManager."""

    def test_conversation_flow(self):
        """Test a complete conversation flow through MemoryManager."""
        manager = MemoryManager()

        manager.add_user_message("Hello")
        manager.add_ai_message("Hi there!")
        manager.add_user_message("How are you?")
        manager.add_ai_message("I'm doing well, thank you!")

        messages = manager.get_messages()
        assert len(messages) == 4
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi there!"
        assert messages[2].content == "How are you?"
        assert messages[3].content == "I'm doing well, thank you!"

    def test_clear_resets_conversation(self):
        """Test that clear resets all conversation history."""
        manager = MemoryManager()
        manager.add_user_message("Message 1")
        manager.add_ai_message("Response 1")

        manager.clear()

        assert len(manager._messages) == 0
        assert manager.get_conversation_context() == ""

    def test_messages_order_preserved(self):
        """Test that message order is preserved in _messages list."""
        manager = MemoryManager()

        manager.add_user_message("First")
        manager.add_ai_message("Second")
        manager.add_user_message("Third")

        assert isinstance(manager._messages[0], HumanMessage)
        assert manager._messages[0].content == "First"
        assert isinstance(manager._messages[1], AIMessage)
        assert manager._messages[1].content == "Second"
        assert isinstance(manager._messages[2], HumanMessage)
        assert manager._messages[2].content == "Third"
