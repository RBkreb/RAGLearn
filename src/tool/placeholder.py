# src/tool/placeholder.py
"""Placeholder Tool - 暂不绑定到 agent"""

from langchain_core.tools import tool


@tool
def placeholder_tool(input: str) -> str:
    """占位符工具，用于后续扩展。

    Args:
        input: 用户输入字符串

    Returns:
        格式化后的响应字符串
    """
    return f"Placeholder tool received: {input}"