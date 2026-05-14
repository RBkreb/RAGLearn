# src/__init__.py
"""LangChain 对话机器人核心模块"""

from .agent import ChatBot
from .tool import placeholder_tool
from .middleware import MiddlewareHooks
from .llm import create_llm
from .config import Settings

__all__ = ["ChatBot", "placeholder_tool", "MiddlewareHooks", "create_llm", "Settings"]