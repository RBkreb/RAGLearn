"""Async auto-summarization module for short-term memory."""

import threading
from typing import Callable, Optional

from langchain_core.messages import AIMessage, HumanMessage


class Summarizer:
    """Handles async summarization of conversation history."""

    def __init__(
        self,
        llm_callable: Callable[[str], str],
        threshold: int = 3000,
    ) -> None:
        """Initialize summarizer.

        Args:
            llm_callable: Function that takes a prompt and returns summary text.
            threshold: Token count threshold to trigger auto-summarization.
        """
        self._llm = llm_callable
        self._threshold = threshold
        self._pending_summary: Optional[str] = None
        self._lock = threading.Lock()
        self._background_thread: Optional[threading.Thread] = None

    def should_summarize(self, token_count: int) -> bool:
        """Check if summarization should be triggered.

        Args:
            token_count: Current token count.

        Returns:
            True if token count exceeds threshold.
        """
        return token_count >= self._threshold

    def summarize_async(
        self,
        messages: list[HumanMessage | AIMessage],
        callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Trigger async summarization in background thread.

        Args:
            messages: List of conversation messages.
            callback: Optional callback when summarization completes.
        """
        with self._lock:
            if self._background_thread is not None and self._background_thread.is_alive():
                return

        conversation_text = self._format_messages(messages)

        def background_task() -> None:
            prompt = f"请简要总结以下对话的核心内容，保留关键信息:\n\n{conversation_text}"
            try:
                summary = self._llm(prompt)
                with self._lock:
                    self._pending_summary = summary
                if callback:
                    callback(summary)
            except Exception:
                pass

        thread = threading.Thread(target=background_task, daemon=True)
        with self._lock:
            self._background_thread = thread
        thread.start()

    def get_pending_summary(self) -> Optional[str]:
        """Get the pending summary if available."""
        with self._lock:
            return self._pending_summary

    def clear_pending(self) -> None:
        """Clear pending summary."""
        with self._lock:
            self._pending_summary = None

    @staticmethod
    def _format_messages(messages: list[HumanMessage | AIMessage]) -> str:
        """Format messages for summarization."""
        parts = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                parts.append(f"用户: {msg.content}")
            elif isinstance(msg, AIMessage):
                parts.append(f"AI: {msg.content}")
        return "\n".join(parts)