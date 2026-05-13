"""Conversation agent with memory integration."""

from typing import Any, Callable, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from ..intent_router import Intent, IntentRouter
from ..safety_checker import SafetyChecker, SafetyResult
from ..short_term_memory import ShortTermMemory
from src.tools.math_tools import add, divide, multiply, subtract


class ConversationAgent:
    """Agent with short-term memory and dynamic tool injection."""

    def __init__(
        self,
        llm_callable: Callable[[list[BaseMessage]], AIMessage],
        short_term_memory: ShortTermMemory,
    ) -> None:
        """Initialize conversation agent.

        Args:
            llm_callable: LLM function that takes messages and returns AI message.
            short_term_memory: ShortTermMemory instance for conversation history.
        """
        self._llm = llm_callable
        self._memory = short_term_memory
        self._router = IntentRouter()
        self._safety = SafetyChecker()
        self._tools: dict[str, BaseTool] = {
            "add": add,
            "subtract": subtract,
            "multiply": multiply,
            "divide": divide,
        }
        self._active_tools: list[BaseTool] = []
        self._last_response: Optional[AIMessage] = None

    def check_safety(self, user_input: str) -> SafetyResult:
        """Check user input for safety concerns.

        Args:
            user_input: Raw user input.

        Returns:
            SafetyResult with safety status.
        """
        return self._safety.check(user_input)

    def process(self, user_input: str) -> str:
        """Process user input and return AI response.

        Args:
            user_input: The user's message.

        Returns:
            AI response text or error message.
        """
        safety_result = self.check_safety(user_input)
        if not safety_result.is_safe:
            return f"无法执行指令: {safety_result.reason}"

        route_result = self._router.route(user_input)

        self._active_tools = []
        if route_result.should_use_tools:
            self._active_tools = list(self._tools.values())

        self._memory.add_user_message(safety_result.sanitized_input)

        messages = self._memory.get_messages()

        system_messages = [route_result.system_prompt]
        all_messages: list[BaseMessage] = system_messages + messages

        if self._active_tools:
            response = self._llm_with_tools(all_messages)
        else:
            response = self._llm(all_messages)

        self._memory.add_ai_message(response.content)
        self._last_response = response

        return response.content

    def _llm_with_tools(self, messages: list[BaseMessage]) -> AIMessage:
        """Call LLM with tools enabled.

        Args:
            messages: All messages including system prompt.

        Returns:
            AI response message.
        """
        tool_descriptions = "\n".join(
            f"- {tool.name}: {tool.description}" for tool in self._active_tools
        )
        tool_prompt = f"\n\n可用工具:\n{tool_descriptions}"
        messages_with_tools = messages.copy()
        if messages_with_tools and isinstance(messages_with_tools[0], SystemMessage):
            messages_with_tools[0] = SystemMessage(
                content=messages_with_tools[0].content + tool_prompt
            )
        return self._llm(messages_with_tools)

    def rewind(self, n: int) -> None:
        """Rewind conversation by n pairs.

        Args:
            n: Number of message pairs to rewind.
        """
        self._memory.rewind(n)

    def repeat(self) -> Optional[str]:
        """Regenerate last AI response.

        Returns:
            The regenerated response text or None.
        """
        last_user = self._memory.get_last_user_message()
        if last_user is None:
            return None

        # Pop the last AI message - user message will be reused
        if self._memory.messages and isinstance(self._memory.messages[-1], AIMessage):
            self._memory.messages.pop()

        # Build messages WITHOUT adding duplicate user message
        messages = self._memory.get_messages()

        system_messages = [self._router.route(last_user).system_prompt]
        all_messages: list[BaseMessage] = system_messages + messages

        # Use same tools as original if applicable
        response = self._llm(all_messages)
        self._memory.add_ai_message(response.content)
        self._last_response = response

        return response.content

    def compact(self, summary: str) -> None:
        """Compact memory with summary.

        Args:
            summary: Summary to replace conversation history.
        """
        self._memory.compact(summary)

    def get_memory(self) -> ShortTermMemory:
        """Get short-term memory instance."""
        return self._memory

    @property
    def token_count(self) -> int:
        """Get current token count."""
        return self._memory.token_count

    @property
    def message_count(self) -> int:
        """Get current message count."""
        return self._memory.message_count()