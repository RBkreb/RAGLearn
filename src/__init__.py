"""Q&A System with prefix-based routing and memory.

This module provides a simple Q&A system with three modes:
- /btw prefix: Direct LLM without memory
- /base prefix: LLM with conversation memory
- No prefix: Use default behavior from config
"""

from src.chain import QAChain
from src.config import Config, DefaultModeConfig, LLMConfig, get_config
from src.router import QueryMode, QueryParser, QueryRouter, ParsedQuery
from src.memory_manager import MemoryManager
from src.llm_service import LLMService

__all__ = [
    "QAChain",
    "Config",
    "DefaultModeConfig",
    "LLMConfig",
    "get_config",
    "QueryMode",
    "QueryParser",
    "QueryRouter",
    "ParsedQuery",
    "MemoryManager",
    "LLMService",
]