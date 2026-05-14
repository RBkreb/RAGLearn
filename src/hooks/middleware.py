# src/hooks/middleware.py
"""LangChain Middleware Hooks - 占位符实现"""

from langchain_core.callbacks import BaseCallbackHandler


class MiddlewareHooks(BaseCallbackHandler):
    """包含所有 LangChain hooks 的占位符实现，每个 hook 触发时打印日志"""

    def on_before_agent(self, **kwargs) -> None:
        print("[Hook] before_agent triggered")

    def on_before_model(self, **kwargs) -> None:
        print("[Hook] before_model triggered")

    def on_after_model(self, response, **kwargs) -> None:
        print(f"[Hook] after_model triggered")

    def on_after_agent(self, **kwargs) -> None:
        print("[Hook] after_agent triggered")

    def on_wrap_model_call(self, **kwargs) -> None:
        print("[Hook] wrap_model_call triggered")

    def on_wrap_tool_call(self, **kwargs) -> None:
        print("[Hook] wrap_tool_call triggered")