"""Tests for intent_router module."""

import pytest

from src.intent_router import Intent, IntentRouter


class TestIntentRouter:
    """Tests for IntentRouter class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self._router = IntentRouter()

    def test_detect_math_keyword(self) -> None:
        """Test math keyword detection."""
        result = self._router.detect_intent("帮我计算 123+456")
        assert result == Intent.MATH

    def test_detect_math_symbols(self) -> None:
        """Test math symbols detection."""
        result = self._router.detect_intent("100 + 200 * 3")
        assert result == Intent.MATH

    def test_detect_normal_conversation(self) -> None:
        """Test normal conversation not detected as math."""
        result = self._router.detect_intent("今天天气怎么样?")
        assert result == Intent.NORMAL

    def test_detect_subtract(self) -> None:
        """Test subtract keyword detection."""
        result = self._router.detect_intent("帮我相减")
        assert result == Intent.MATH

    def test_detect_multiply(self) -> None:
        """Test multiply keyword detection."""
        result = self._router.detect_intent("数字相乘")
        assert result == Intent.MATH

    def test_detect_divide(self) -> None:
        """Test divide keyword detection."""
        result = self._router.detect_intent("除以")
        assert result == Intent.MATH

    def test_route_math_prompt(self) -> None:
        """Test routing to math prompt."""
        result = self._router.route("计算 5+3")
        assert result.should_use_tools is True
        assert result.intent == Intent.MATH
        assert "数学" in result.system_prompt.content

    def test_route_normal_prompt(self) -> None:
        """Test routing to normal prompt."""
        result = self._router.route("你好")
        assert result.should_use_tools is False
        assert result.intent == Intent.NORMAL

    def test_current_prompt_property(self) -> None:
        """Test current prompt property."""
        self._router.route("测试")
        assert isinstance(self._router.current_prompt, str)

    def test_multiple_math_symbols(self) -> None:
        """Test detection with multiple math symbols."""
        result = self._router.detect_intent("1+2-3*4")
        assert result == Intent.MATH

    def test_single_math_symbol_not_math(self) -> None:
        """Test that single math symbol doesn't trigger math intent."""
        result = self._router.detect_intent("+ is a symbol")
        assert result == Intent.NORMAL