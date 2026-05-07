"""LLM service for ChatOpenAI with tool support."""

from dataclasses import dataclass
from typing import Any

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

from src.config import get_config


@dataclass
class LLMResult:
    """Result from LLM generation with optional tool calls.

    Attributes:
        content: The text content of the response.
        tool_calls: List of tool calls made during generation, if any.
    """

    content: str
    tool_calls: list | None = None


class LLMService:
    """Service for LLM invocation via ChatOpenAI with tool support.

    All methods use the tool-enabled agent which autonomously decides
    when to call tools based on query content and tool descriptions.
    """

    def __init__(self) -> None:
        """Initialize LLM service with lazy loading."""
        self._llm: ChatOpenAI | None = None
        self._agent: Any | None = None

    def _get_llm(self) -> ChatOpenAI:
        """Get or create ChatOpenAI instance.

        Returns:
            ChatOpenAI LLM instance.
        """
        if self._llm is None:
            config = get_config()
            self._llm = ChatOpenAI(
                model=config.llm.model,
                temperature=config.llm.temperature,
                max_tokens=config.llm.max_tokens,
                base_url=config.llm.base_url,
                api_key=config.llm.api_key,
            )
        return self._llm

    def _get_agent(self) -> Any:
        """Get or create agent with bound math tools.

        The agent autonomously decides when to call tools based on
        the system prompt and tool descriptions.

        Returns:
            Agent instance with bound math tools.
        """
        if self._agent is None:
            config = get_config()
            llm = self._get_llm()

            # Import all available tools
            from src.tools.math_tools import add, subtract, multiply, divide
            from src.tools.rag_tool import rag_retrieve

            # Build tool registry
            tool_registry = {
                "add": add,
                "subtract": subtract,
                "multiply": multiply,
                "divide": divide,
                "rag_retrieve": rag_retrieve,
            }

            # Get tools from config
            tools = [tool_registry[name] for name in config.agent.tools]

            self._agent = create_agent(
                model=llm,
                tools=tools,
                system_prompt=SystemMessage(content=config.agent.system_prompt),
            )
        return self._agent

    def _extract_tool_calls(self, result: dict[str, Any]) -> list | None:
        """Extract tool calls from agent result.

        Args:
            result: Agent invoke result dict.

        Returns:
            List of tool calls if present, None otherwise.
        """
        messages = result.get("messages", [])
        # Find the last AIMessage with tool_calls
        tool_calls = None
        for msg in reversed(messages):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls = msg.tool_calls
                break
        return tool_calls

    def generate(self, query: str) -> LLMResult:
        """Generate response using tool-enabled agent.

        The agent autonomously decides when to call tools.

        Args:
            query: User query.

        Returns:
            LLMResult containing response content and any tool calls made.
        """
        agent = self._get_agent()
        result = agent.invoke({"messages": [("user", query)]})
        last_msg = result["messages"][-1]
        tool_calls = self._extract_tool_calls(result)
        return LLMResult(content=last_msg.content, tool_calls=tool_calls)

    def generate_with_messages(
        self, messages: list[BaseMessage]
    ) -> LLMResult:
        """Generate response with full message history.

        The agent autonomously decides when to call tools.

        Args:
            messages: List of messages in conversation order.

        Returns:
            LLMResult containing response content and any tool calls made.
        """
        agent = self._get_agent()
        result = agent.invoke({"messages": messages})
        last_msg = result["messages"][-1]
        tool_calls = self._extract_tool_calls(result)
        return LLMResult(content=last_msg.content, tool_calls=tool_calls)