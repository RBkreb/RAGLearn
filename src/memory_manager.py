"""Short-term memory management using LangChain messages."""

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from typing import Sequence


class MemoryManager:
    """Manages short-term conversation memory using LangChain messages.

    Stores conversation history as a sequence of messages in order:
    HumanMessage -> AIMessage -> HumanMessage -> AIMessage ...
    """

    def __init__(self) -> None:
        """Initialize empty conversation history."""
        self._messages: list[BaseMessage] = []

    def add_user_message(self, message: str) -> None:
        """Add a user message to conversation history.

        Args:
            message: User's message content.
        """
        self._messages.append(HumanMessage(content=message))

    def add_ai_message(self, message: str, tool_calls: list | None = None) -> None:
        """Add an AI message to conversation history.

        Args:
            message: AI's response content.
            tool_calls: Optional list of tool calls made by the AI (not stored in message).
        """
        self._messages.append(AIMessage(content=message))

    def get_messages(self) -> Sequence[BaseMessage]:
        """Get all conversation messages.

        Returns:
            Sequence of all messages in conversation history.
        """
        return self._messages

    def clear(self) -> None:
        """Clear all conversation history."""
        self._messages.clear()

    def get_conversation_context(self) -> str:
        """Get conversation history as a formatted string.

        Returns:
            String containing all messages in "User: ...\nAssistant: ..." format.
        """
        context_parts = []
        for msg in self._messages:
            if isinstance(msg, HumanMessage):
                context_parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                context_parts.append(f"Assistant: {msg.content}")
        return "\n".join(context_parts)

    def save_context(
        self, query: str, response: str, tool_calls: list | None = None
    ) -> None:
        """Save user query and AI response to memory.

        Args:
            query: User's message.
            response: AI's response.
            tool_calls: Optional list of tool calls made by the AI.
        """
        self.add_user_message(query)
        self.add_ai_message(response, tool_calls)

    def should_use_memory(self, mode) -> bool:
        """Check if memory should be used for given mode.

        Args:
            mode: Query mode to check.

        Returns:
            True if memory should be used, False otherwise.
        """
        from src.router import QueryMode

        return mode == QueryMode.BASE