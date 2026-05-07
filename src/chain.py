"""Main Q&A chain orchestrator."""

from langchain_core.messages import HumanMessage, SystemMessage

from src.config import get_config
from src.router import QueryMode, QueryRouter
from src.memory_manager import MemoryManager
from src.llm_service import LLMService, LLMResult


class QAChain:
    """Main Q&A chain with prefix routing and tool support."""

    def __init__(self) -> None:
        """Initialize Q&A chain with all components."""
        self._router = QueryRouter()
        self._memory = MemoryManager()
        self._llm_service = LLMService()
        self._config = get_config()

    def invoke(self, query: str) -> str:
        """Process query and return response.

        All queries are processed through the tool-enabled agent.
        The agent autonomously decides when to call tools based on
        query content and tool descriptions.

        Routing logic:
        - /btw prefix: Direct agent call without memory
        - /base prefix: Agent call with conversation memory as context
        - No prefix: Uses config default behavior

        Args:
            query: User's query, possibly with prefix.

        Returns:
            Formatted response string, including tool calls if used.
        """
        parsed = self._router.route(query)

        if parsed.mode == QueryMode.DIRECT:
            result = self._llm_service.generate(parsed.content)
            return self._format_response(result)

        elif parsed.mode == QueryMode.BASE:
            messages = self._build_messages(parsed.content)
            result = self._llm_service.generate_with_messages(messages)
            self._memory.save_context(parsed.content, result.content, result.tool_calls)
            return self._format_response(result)

        else:
            # DEFAULT mode - use config default
            if self._config.default_mode.mode == "base":
                messages = self._build_messages(parsed.content)
                result = self._llm_service.generate_with_messages(messages)
                self._memory.save_context(parsed.content, result.content, result.tool_calls)
                return self._format_response(result)
            else:
                result = self._llm_service.generate(parsed.content)
                return self._format_response(result)

    def _build_messages(self, query: str) -> list:
        """Build message list from memory and new query.

        Args:
            query: User's query.

        Returns:
            List of messages in conversation order.
        """
        messages = list(self._memory.get_messages())
        messages.append(HumanMessage(content=query))
        return messages

    def _format_response(self, result: LLMResult) -> str:
        """Format LLM result for output.

        Args:
            result: LLMResult from service.

        Returns:
            Formatted string with content and tool calls if present.
        """
        output = result.content
        if result.tool_calls:
            tool_names = [tc.get("name", str(tc)) for tc in result.tool_calls]
            output += f"\n\n[使用工具: {', '.join(tool_names)}]"
        return output

    def clear_memory(self) -> None:
        """Clear conversation memory."""
        self._memory.clear()

    def get_memory_context(self) -> str:
        """Get current memory context string.

        Returns:
            Current conversation context.
        """
        return self._memory.get_conversation_context()