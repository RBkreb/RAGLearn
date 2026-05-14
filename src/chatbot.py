# src/chatbot.py
"""LangChain 对话机器人 - 最小实现"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .hooks import MiddlewareHooks


class ChatBot:
    """包含所有 middleware hooks 的对话机器人"""

    def __init__(
        self,
        model_name: str = "qwen3.5-0.8b",
        base_url: str = "http://127.0.0.1:1234",
    ) -> None:
        """初始化 ChatBot。

        Args:
            model_name: 模型名称
            base_url: LLM 服务地址
        """
        self.model_name = model_name
        self.base_url = base_url
        self._hooks = MiddlewareHooks()
        self._llm = ChatOpenAI(
            model=model_name,
            base_url=base_url,
            api_key="dummy",
            callbacks=[self._hooks],
        )

    def chat(self, user_input: str) -> str:
        """处理单轮对话。

        Args:
            user_input: 用户输入

        Returns:
            AI 回复内容
        """
        self._hooks.on_before_agent()
        self._hooks.on_before_model()

        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content=user_input),
        ]
        response = self._llm.invoke(messages)

        self._hooks.on_after_model(response)
        self._hooks.on_after_agent()

        return response.content