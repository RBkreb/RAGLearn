"""Unit tests for chain.py - QAChain."""

from unittest.mock import MagicMock, patch

import pytest

from src.chain import QAChain
from src.router import QueryMode
from src.llm_service import LLMResult


class TestQAChainInit:
    """Tests for QAChain initialization."""

    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    @patch("src.chain.get_config")
    def test_init_creates_all_components(
        self, mock_get_config, mock_router_cls, mock_llm_cls, mock_memory_cls
    ):
        """Test __init__ creates router, memory, and llm_service."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory_cls.return_value = mock_memory

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()

        mock_router_cls.assert_called_once()
        mock_memory_cls.assert_called_once()
        mock_llm_cls.assert_called_once()
        mock_get_config.assert_called_once()

        assert chain._router == mock_router
        assert chain._memory == mock_memory
        assert chain._llm_service == mock_llm
        assert chain._config == mock_config


class TestQAChainInvokeDirectMode:
    """Tests for QAChain.invoke() with DIRECT mode (/btw prefix)."""

    @patch("src.chain.get_config")
    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    def test_invoke_direct_mode_uses_generate(
        self, mock_router_cls, mock_llm_cls, mock_memory_cls, mock_get_config
    ):
        """Test /btw prefix routes to generate() without memory."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        from src.router import ParsedQuery
        mock_router.route.return_value = ParsedQuery(
            mode=QueryMode.DIRECT, content="direct query"
        )
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory_cls.return_value = mock_memory

        mock_llm = MagicMock()
        mock_llm.generate.return_value = LLMResult(content="direct response", tool_calls=None)
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()
        result = chain.invoke("/btw direct query")

        mock_llm.generate.assert_called_once_with("direct query")
        mock_memory.get_conversation_context.assert_not_called()
        mock_memory.save_context.assert_not_called()
        assert result == "direct response"

    @patch("src.chain.get_config")
    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    def test_invoke_direct_mode_does_not_save_to_memory(
        self, mock_router_cls, mock_llm_cls, mock_memory_cls, mock_get_config
    ):
        """Test DIRECT mode does not save to conversation memory."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        from src.router import ParsedQuery
        mock_router.route.return_value = ParsedQuery(
            mode=QueryMode.DIRECT, content="test"
        )
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory_cls.return_value = mock_memory

        mock_llm = MagicMock()
        mock_llm.generate.return_value = LLMResult(content="response", tool_calls=None)
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()
        chain.invoke("/btw test")

        mock_memory.save_context.assert_not_called()
        mock_memory.add_user_message.assert_not_called()
        mock_memory.add_ai_message.assert_not_called()


class TestQAChainInvokeBaseMode:
    """Tests for QAChain.invoke() with BASE mode (/base prefix)."""

    @patch("src.chain.get_config")
    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    def test_invoke_base_mode_with_context(
        self, mock_router_cls, mock_llm_cls, mock_memory_cls, mock_get_config
    ):
        """Test /base prefix with existing context uses generate_with_messages."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        from src.router import ParsedQuery
        mock_router.route.return_value = ParsedQuery(
            mode=QueryMode.BASE, content="base query"
        )
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory.get_messages.return_value = []
        mock_memory_cls.return_value = mock_memory

        mock_llm = MagicMock()
        mock_llm.generate_with_messages.return_value = LLMResult(
            content="contextual response", tool_calls=None
        )
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()
        result = chain.invoke("/base base query")

        mock_memory.get_messages.assert_called_once()
        mock_llm.generate_with_messages.assert_called_once()
        mock_llm.generate.assert_not_called()
        mock_memory.save_context.assert_called_once_with(
            "base query", "contextual response", None
        )
        assert result == "contextual response"

    @patch("src.chain.get_config")
    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    def test_invoke_base_mode_always_uses_generate_with_messages(
        self, mock_router_cls, mock_llm_cls, mock_memory_cls, mock_get_config
    ):
        """Test /base prefix always uses generate_with_messages even with empty context."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        from src.router import ParsedQuery
        mock_router.route.return_value = ParsedQuery(
            mode=QueryMode.BASE, content="base query"
        )
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory.get_messages.return_value = []
        mock_memory_cls.return_value = mock_memory

        mock_llm = MagicMock()
        mock_llm.generate_with_messages.return_value = LLMResult(
            content="contextual response", tool_calls=None
        )
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()
        result = chain.invoke("/base base query")

        mock_llm.generate_with_messages.assert_called_once()
        mock_llm.generate.assert_not_called()
        mock_memory.save_context.assert_called_once_with(
            "base query", "contextual response", None
        )
        assert result == "contextual response"


class TestQAChainInvokeDefaultMode:
    """Tests for QAChain.invoke() with DEFAULT mode (no prefix)."""

    @patch("src.chain.get_config")
    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    def test_invoke_default_mode_direct_config(
        self, mock_router_cls, mock_llm_cls, mock_memory_cls, mock_get_config
    ):
        """Test no prefix with direct config uses generate()."""
        mock_config = MagicMock()
        mock_config.default_mode.mode = "direct"
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        from src.router import ParsedQuery
        mock_router.route.return_value = ParsedQuery(
            mode=QueryMode.DEFAULT, content="default query"
        )
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory_cls.return_value = mock_memory

        mock_llm = MagicMock()
        mock_llm.generate.return_value = LLMResult(content="direct response", tool_calls=None)
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()
        result = chain.invoke("default query")

        mock_llm.generate.assert_called_once_with("default query")
        mock_memory.save_context.assert_not_called()
        assert result == "direct response"

    @patch("src.chain.get_config")
    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    def test_invoke_default_mode_base_config_with_context(
        self, mock_router_cls, mock_llm_cls, mock_memory_cls, mock_get_config
    ):
        """Test no prefix with base config and context uses generate_with_messages."""
        mock_config = MagicMock()
        mock_config.default_mode.mode = "base"
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        from src.router import ParsedQuery
        mock_router.route.return_value = ParsedQuery(
            mode=QueryMode.DEFAULT, content="default query"
        )
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory.get_messages.return_value = []
        mock_memory_cls.return_value = mock_memory

        mock_llm = MagicMock()
        mock_llm.generate_with_messages.return_value = LLMResult(
            content="base response", tool_calls=None
        )
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()
        result = chain.invoke("default query")

        mock_llm.generate_with_messages.assert_called_once()
        mock_memory.save_context.assert_called_once_with(
            "default query", "base response", None
        )
        assert result == "base response"

    @patch("src.chain.get_config")
    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    def test_invoke_default_mode_base_config_always_uses_generate_with_messages(
        self, mock_router_cls, mock_llm_cls, mock_memory_cls, mock_get_config
    ):
        """Test no prefix with base config always uses generate_with_messages."""
        mock_config = MagicMock()
        mock_config.default_mode.mode = "base"
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        from src.router import ParsedQuery
        mock_router.route.return_value = ParsedQuery(
            mode=QueryMode.DEFAULT, content="default query"
        )
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory.get_messages.return_value = []
        mock_memory_cls.return_value = mock_memory

        mock_llm = MagicMock()
        mock_llm.generate_with_messages.return_value = LLMResult(
            content="base response", tool_calls=None
        )
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()
        result = chain.invoke("default query")

        mock_llm.generate_with_messages.assert_called_once()
        mock_llm.generate.assert_not_called()
        mock_memory.save_context.assert_called_once_with(
            "default query", "base response", None
        )
        assert result == "base response"


class TestQAChainClearMemory:
    """Tests for clear_memory method."""

    @patch("src.chain.get_config")
    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    def test_clear_memory_calls_memory_clear(
        self, mock_router_cls, mock_llm_cls, mock_memory_cls, mock_get_config
    ):
        """Test clear_memory delegates to _memory.clear()."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory_cls.return_value = mock_memory

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()
        chain.clear_memory()

        mock_memory.clear.assert_called_once()


class TestQAChainGetMemoryContext:
    """Tests for get_memory_context method."""

    @patch("src.chain.get_config")
    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    def test_get_memory_context_returns_memory_context(
        self, mock_router_cls, mock_llm_cls, mock_memory_cls, mock_get_config
    ):
        """Test get_memory_context returns _memory.get_conversation_context()."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory.get_conversation_context.return_value = "conversation string"
        mock_memory_cls.return_value = mock_memory

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()
        result = chain.get_memory_context()

        mock_memory.get_conversation_context.assert_called_once()
        assert result == "conversation string"


class TestQAChainEdgeCases:
    """Edge case tests for QAChain."""

    @patch("src.chain.get_config")
    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    def test_invoke_with_empty_query_direct_mode(
        self, mock_router_cls, mock_llm_cls, mock_memory_cls, mock_get_config
    ):
        """Test invoke with empty query in DIRECT mode."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        from src.router import ParsedQuery
        mock_router.route.return_value = ParsedQuery(mode=QueryMode.DIRECT, content="")
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory_cls.return_value = mock_memory

        mock_llm = MagicMock()
        mock_llm.generate.return_value = LLMResult(content="empty response", tool_calls=None)
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()
        result = chain.invoke("/btw ")

        mock_llm.generate.assert_called_once_with("")
        assert result == "empty response"

    @patch("src.chain.get_config")
    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    def test_invoke_with_empty_query_base_mode(
        self, mock_router_cls, mock_llm_cls, mock_memory_cls, mock_get_config
    ):
        """Test invoke with empty query in BASE mode."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        from src.router import ParsedQuery
        mock_router.route.return_value = ParsedQuery(mode=QueryMode.BASE, content="")
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory.get_messages.return_value = []
        mock_memory_cls.return_value = mock_memory

        mock_llm = MagicMock()
        mock_llm.generate_with_messages.return_value = LLMResult(
            content="contextual empty", tool_calls=None
        )
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()
        result = chain.invoke("/base ")

        mock_llm.generate_with_messages.assert_called_once()
        assert result == "contextual empty"

    @patch("src.chain.get_config")
    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    def test_multiple_invocations_accumulate_memory(
        self, mock_router_cls, mock_llm_cls, mock_memory_cls, mock_get_config
    ):
        """Test multiple invokes in BASE mode accumulate context."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        from src.router import ParsedQuery
        mock_router.route.return_value = ParsedQuery(mode=QueryMode.BASE, content="query")
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory.get_messages.return_value = []
        mock_memory_cls.return_value = mock_memory

        mock_llm = MagicMock()
        mock_llm.generate_with_messages.return_value = LLMResult(
            content="response", tool_calls=None
        )
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()

        chain.invoke("/base query")
        chain.invoke("/base query")

        assert mock_memory.save_context.call_count == 2
        assert mock_memory.get_messages.call_count == 2


class TestQAChainToolCalls:
    """Tests for tool call handling in QAChain."""

    @patch("src.chain.get_config")
    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    def test_invoke_direct_mode_with_tool_calls(
        self, mock_router_cls, mock_llm_cls, mock_memory_cls, mock_get_config
    ):
        """Test DIRECT mode response includes tool call info."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        from src.router import ParsedQuery
        mock_router.route.return_value = ParsedQuery(
            mode=QueryMode.DIRECT, content="calculate 2+2"
        )
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory_cls.return_value = mock_memory

        mock_llm = MagicMock()
        mock_llm.generate.return_value = LLMResult(
            content="The result is 4.",
            tool_calls=[{"name": "add", "args": {"a": 2, "b": 2}}]
        )
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()
        result = chain.invoke("/btw calculate 2+2")

        expected = "The result is 4.\n\n[使用工具: add]"
        assert result == expected

    @patch("src.chain.get_config")
    @patch("src.chain.MemoryManager")
    @patch("src.chain.LLMService")
    @patch("src.chain.QueryRouter")
    def test_invoke_base_mode_saves_tool_calls_to_memory(
        self, mock_router_cls, mock_llm_cls, mock_memory_cls, mock_get_config
    ):
        """Test BASE mode saves tool calls to memory."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_router = MagicMock()
        from src.router import ParsedQuery
        mock_router.route.return_value = ParsedQuery(
            mode=QueryMode.BASE, content="calculate 2+2"
        )
        mock_router_cls.return_value = mock_router

        mock_memory = MagicMock()
        mock_memory.get_messages.return_value = []
        mock_memory_cls.return_value = mock_memory

        tool_calls = [{"name": "add", "args": {"a": 2, "b": 2}}]
        mock_llm = MagicMock()
        mock_llm.generate_with_messages.return_value = LLMResult(
            content="The result is 4.",
            tool_calls=tool_calls
        )
        mock_llm_cls.return_value = mock_llm

        chain = QAChain()
        result = chain.invoke("/base calculate 2+2")

        mock_memory.save_context.assert_called_once_with(
            "calculate 2+2", "The result is 4.", tool_calls
        )
        assert result == "The result is 4.\n\n[使用工具: add]"
