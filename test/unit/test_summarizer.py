"""Tests for summarizer module."""

import threading
from unittest.mock import MagicMock

import pytest

from src.summarizer import Summarizer


class TestSummarizer:
    """Tests for Summarizer class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self._llm_mock = MagicMock(return_value="Test summary")
        self._summarizer = Summarizer(
            llm_callable=self._llm_mock,
            threshold=100,
        )

    def test_should_summarize_below_threshold(self) -> None:
        """Test that summarization is not triggered below threshold."""
        result = self._summarizer.should_summarize(50)
        assert result is False

    def test_should_summarize_at_threshold(self) -> None:
        """Test that summarization is triggered at threshold."""
        result = self._summarizer.should_summarize(100)
        assert result is True

    def test_should_summarize_above_threshold(self) -> None:
        """Test that summarization is triggered above threshold."""
        result = self._summarizer.should_summarize(200)
        assert result is True

    def test_summarize_async(self) -> None:
        """Test async summarization."""
        from langchain_core.messages import HumanMessage

        messages = [HumanMessage(content="Test message")]
        callback_called = []

        def callback(summary: str) -> None:
            callback_called.append(summary)

        self._summarizer.summarize_async(messages, callback)

        self._summarizer._background_thread.join(timeout=2)
        assert len(callback_called) == 1
        assert callback_called[0] == "Test summary"

    def test_get_pending_summary(self) -> None:
        """Test getting pending summary."""
        result = self._summarizer.get_pending_summary()
        assert result is None

    def test_clear_pending(self) -> None:
        """Test clearing pending summary."""
        self._summarizer._pending_summary = "test"
        self._summarizer.clear_pending()
        assert self._summarizer.get_pending_summary() is None

    def test_format_messages(self) -> None:
        """Test formatting messages for summarization."""
        from langchain_core.messages import AIMessage, HumanMessage

        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there"),
        ]
        formatted = Summarizer._format_messages(messages)
        assert "用户:" in formatted
        assert "AI:" in formatted

    def test_concurrent_summarize_async(self) -> None:
        """Test that concurrent summarization doesn't start new thread if one is running."""
        self._llm_mock.side_effect = lambda x: threading.Event().wait(1) or "summary"

        from langchain_core.messages import HumanMessage

        messages = [HumanMessage(content="Test")]
        self._summarizer.summarize_async(messages)

        self._summarizer._background_thread.join(timeout=0.5)
        second_thread = self._summarizer._background_thread

        self._summarizer.summarize_async(messages)

        assert self._summarizer._background_thread is second_thread or self._summarizer._background_thread.is_alive()