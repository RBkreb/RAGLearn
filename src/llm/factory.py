# src/llm/factory.py
"""LLM 工厂函数"""

from langchain_openai import ChatOpenAI

from ..config.settings import Settings


def create_llm(settings: Settings | None = None) -> ChatOpenAI:
    """创建 LLM 实例。

    Args:
        settings: 配置对象，默认使用 DEFAULT_SETTINGS

    Returns:
        ChatOpenAI 实例
    """
    if settings is None:
        from ..config.settings import DEFAULT_SETTINGS
        settings = DEFAULT_SETTINGS

    return ChatOpenAI(
        model=settings.model_name,
        base_url=settings.base_url,
        api_key=settings.api_key,
    )