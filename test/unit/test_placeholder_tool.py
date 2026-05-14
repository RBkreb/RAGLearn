# test/unit/test_placeholder_tool.py
import pytest
from src.tools.placeholder import placeholder_tool


def test_placeholder_tool_returns_input():
    """验证占位符工具返回格式化后的输入"""
    result = placeholder_tool.invoke("hello")
    assert result == "Placeholder tool received: hello"