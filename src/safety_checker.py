"""Safety input filter for user messages."""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class SafetyResult:
    """Result of safety check."""

    is_safe: bool
    reason: Optional[str]
    sanitized_input: str


class SafetyChecker:
    """Checks user input for safety concerns."""

    DANGEROUS_PATTERNS = [
        r"rm\s+-rf",
        r"del\s+/[fqs]",
        r"format\s+[a-z]:",
        r"mkfs",
        r"drop\s+table",
        r"delete\s+from",
        r"exec\s*\(",
        r"eval\s*\(",
        r"__import__",
        r"os\.system",
        r"subprocess",
        r"system\s*\(",
        r"shell\s*=",
        r">\s*/dev/",
        r"&\s*;\s*rm",
    ]

    INJECT_PATTERNS = [
        r"ignore\s+(previous|above|below)",
        r"disregard\s+(previous|above|below)",
        r"forget\s+(previous|above|below)",
        r"system\s*:\s*",
        r"you\s+are\s+now\s+",
        r"act\s+as\s+",
        r"pretend\s+you\s+are",
        r"new\s+instructions?",
    ]

    SENSITIVE_INTENTS = [
        r"steal\s+password",
        r"hack\s+",
        r"crack\s+",
        r"bypass\s+(security|auth)",
        r"extract\s+(key|token|secret)",
    ]

    def __init__(self) -> None:
        """Initialize safety checker."""
        self._dangerous_regex = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]
        self._inject_regex = [re.compile(p, re.IGNORECASE) for p in self.INJECT_PATTERNS]
        self._sensitive_regex = [re.compile(p, re.IGNORECASE) for p in self.SENSITIVE_INTENTS]

    def check(self, user_input: str) -> SafetyResult:
        """Check input for safety concerns.

        Args:
            user_input: The raw user input.

        Returns:
            SafetyResult with is_safe, reason, and sanitized_input.
        """
        sanitized = user_input.strip()

        for pattern in self._dangerous_regex:
            if pattern.search(sanitized):
                return SafetyResult(
                    is_safe=False,
                    reason="检测到危险命令",
                    sanitized_input=sanitized,
                )

        for pattern in self._inject_regex:
            if pattern.search(sanitized):
                return SafetyResult(
                    is_safe=False,
                    reason="检测到提示注入攻击",
                    sanitized_input=sanitized,
                )

        for pattern in self._sensitive_regex:
            if pattern.search(sanitized):
                return SafetyResult(
                    is_safe=False,
                    reason="检测到敏感信息获取意图",
                    sanitized_input=sanitized,
                )

        if len(sanitized) > 10000:
            sanitized = sanitized[:10000]

        return SafetyResult(is_safe=True, reason=None, sanitized_input=sanitized)