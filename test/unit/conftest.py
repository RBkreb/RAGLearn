"""Shared pytest fixtures for unit tests."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_chat_llama():
    """Create a mock ChatLlamaCpp instance."""
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Mocked LLM response"
    mock_llm.invoke.return_value = mock_response
    mock_llm.stream.return_value = iter(["chunk1", "chunk2"])
    return mock_llm


@pytest.fixture
def mock_config():
    """Create a mock Config instance."""
    mock_cfg = MagicMock()
    mock_cfg.llm.model_path = "test/model path"
    mock_cfg.llm.temperature = 0.7
    mock_cfg.llm.max_tokens = 1024
    mock_cfg.llm.n_ctx = 2048
    mock_cfg.default_mode.mode = "direct"
    mock_cfg.default_mode.temperature = 0.7
    mock_cfg.default_mode.max_tokens = 1024
    return mock_cfg


@pytest.fixture
def mock_chat_message_history():
    """Create a mock ChatMessageHistory instance."""
    from langchain_core.messages import HumanMessage, AIMessage

    mock_history = MagicMock()
    mock_history.messages = []
    return mock_history
