"""Short-term memory module for conversation context."""

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


@dataclass
class ShortTermMemory:
    """Manages conversation history for a single session."""

    session_id: str
    messages: list[SystemMessage | HumanMessage | AIMessage] = field(default_factory=list)
    _token_count: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _session_name: Optional[str] = None

    def add_user_message(self, content: str) -> None:
        """Add a user message to memory.

        Args:
            content: The user message content.
        """
        with self._lock:
            self.messages.append(HumanMessage(content=content))
            self._token_count += self._estimate_tokens(content)

    def add_ai_message(self, content: str) -> None:
        """Add an AI message to memory.

        Args:
            content: The AI message content.
        """
        with self._lock:
            self.messages.append(AIMessage(content=content))
            self._token_count += self._estimate_tokens(content)

    def get_messages(self) -> list[SystemMessage | HumanMessage | AIMessage]:
        """Get all messages."""
        with self._lock:
            return list(self.messages)

    def get_last_user_message(self) -> Optional[str]:
        """Get the last user message content."""
        with self._lock:
            for msg in reversed(self.messages):
                if isinstance(msg, HumanMessage):
                    return msg.content
            return None

    def get_last_ai_message(self) -> Optional[str]:
        """Get the last AI message content."""
        with self._lock:
            for msg in reversed(self.messages):
                if isinstance(msg, AIMessage):
                    return msg.content
            return None

    def rewind(self, n: int) -> None:
        """Remove the last n pairs of user+AI messages.

        Args:
            n: Number of message pairs to remove.
        """
        with self._lock:
            removed = 0
            while removed < n and len(self.messages) > 0:
                if len(self.messages) >= 2:
                    if (isinstance(self.messages[-1], AIMessage) and
                        isinstance(self.messages[-2], HumanMessage)):
                        self.messages.pop()
                        self.messages.pop()
                        removed += 1
                    else:
                        break
                else:
                    break

    def compact(self, summary: str) -> None:
        """Replace conversation history with a summary.

        Args:
            summary: The summarized content to replace history.
        """
        with self._lock:
            self.messages = [SystemMessage(content=f"会话摘要: {summary}")]
            self._token_count = self._estimate_tokens(summary) + 50

    def clear(self) -> None:
        """Clear all messages."""
        with self._lock:
            self.messages.clear()
            self._token_count = 0

    def save(self, path: Path) -> None:
        """Save memory to JSON file.

        Args:
            path: Path to save the memory.
        """
        with self._lock:
            data = {
                "session_id": self.session_id,
                "messages": [
                    {"type": type(m).__name__, "content": m.content}
                    for m in self.messages
                ],
                "token_count": self._token_count,
                "session_name": getattr(self, '_session_name', None),
            }
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: Path) -> "ShortTermMemory":
        """Load memory from JSON file.

        Args:
            path: Path to load the memory from.

        Returns:
            Loaded ShortTermMemory instance.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        messages = []
        for m in data["messages"]:
            if m["type"] == "HumanMessage":
                messages.append(HumanMessage(content=m["content"]))
            elif m["type"] == "AIMessage":
                messages.append(AIMessage(content=m["content"]))
            elif m["type"] == "SystemMessage":
                messages.append(SystemMessage(content=m["content"]))

        instance = cls(session_id=data["session_id"], messages=messages)
        instance._token_count = data.get("token_count", 0)
        instance._session_name = data.get("session_name")
        return instance

    @property
    def token_count(self) -> int:
        """Get estimated token count."""
        return self._token_count

    def message_count(self) -> int:
        """Get number of messages."""
        return len(self.messages)

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count (rough approximation)."""
        return len(text) // 4