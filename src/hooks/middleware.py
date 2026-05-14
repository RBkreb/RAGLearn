# src/hooks/middleware.py
"""LangChain Middleware Hooks - 占位符实现"""

from langchain.agents.middleware import AgentMiddleware,ModelRequest,ToolCallRequest

class MiddlewareHooks(AgentMiddleware):
    """包含所有 LangChain hooks 的占位符实现，每个 hook 触发时打印日志"""
    
    def before_agent(self,state):
        print("[Hook] before_agent triggered")

    def before_model(self,state):
        print("[Hook] before_model triggered")

    def after_model(self,state):
        print(f"[Hook] after_model triggered")

    def after_agent(self,state):
        print("[Hook] after_agent triggered")

    def wrap_model_call(self,request:ModelRequest,handler):
        print("[Hook] wrap_model_call triggered")
        return handler(request)

    def wrap_tool_call(self,request:ToolCallRequest,handler):
        print("[Hook] wrap_tool_call triggered")
        return handler(request)