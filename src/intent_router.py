"""Intent router for dynamic prompt and tool switching."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from langchain_core.messages import SystemMessage


class Intent(Enum):
    """Detected user intent."""

    MATH = "math"
    NORMAL = "normal"
    UNKNOWN = "unknown"


@dataclass
class RouterResult:
    """Result of intent routing."""

    intent: Intent
    system_prompt: SystemMessage
    should_use_tools: bool


MATH_KEYWORDS = [
    r"计算",
    r"相加",
    r"相减",
    r"相乘",
    r"除以",
    r"加\s*\d",
    r"减\s*\d",
    r"乘以",
    r"\d+\s*\+\s*\d",
    r"\d+\s*-\s*\d",
    r"\d+\s*\*\s*\d",
    r"\d+\s*/\s*\d",
    r"求和",
    r"等于多少",
    r"是多少",
]

DEFAULT_PROMPT = """你是一个友好的AI助手，请根据用户的问题给出准确的回答。"""

MATH_PROMPT = """你是一个数学计算助手。请仔细计算用户提出的数学问题，并给出准确的答案。

计算规则：
- 加法：直接相加
- 减法：减去第二个数
- 乘法：相乘
- 除法：除以非零数

如果用户要求的计算超出这些范围，请先说明再进行计算。"""


class IntentRouter:
    """Routes user input to appropriate prompt and tools."""

    def __init__(self) -> None:
        """Initialize router."""
        self._math_patterns = [re.compile(p, re.IGNORECASE) for p in MATH_KEYWORDS]
        self._current_prompt = DEFAULT_PROMPT

    def detect_intent(self, user_input: str) -> Intent:
        """Detect user intent from input.

        Args:
            user_input: The user's input message.

        Returns:
            Detected Intent enum value.
        """
        for pattern in self._math_patterns:
            if pattern.search(user_input):
                return Intent.MATH

        math_symbols = re.findall(r"[\+\-\*/]", user_input)
        if len(math_symbols) >= 2 and any(c.isdigit() for c in user_input):
            return Intent.MATH

        return Intent.NORMAL

    def route(self, user_input: str) -> RouterResult:
        """Route user input to appropriate prompt and tools.

        Args:
            user_input: The user's input message.

        Returns:
            RouterResult with intent, system prompt, and tool flag.
        """
        intent = self.detect_intent(user_input)

        if intent == Intent.MATH:
            prompt = MATH_PROMPT
            should_use_tools = True
        else:
            prompt = DEFAULT_PROMPT
            should_use_tools = False

        self._current_prompt = prompt
        return RouterResult(
            intent=intent,
            system_prompt=SystemMessage(content=prompt),
            should_use_tools=should_use_tools,
        )

    @property
    def current_prompt(self) -> str:
        """Get current system prompt text."""
        return self._current_prompt