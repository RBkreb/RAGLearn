# src/main.py
"""LangChain 对话机器人入口"""

from src.agent.chatbot import ChatBot


def main(user_input: str) -> str:
    """执行单轮对话。

    Args:
        user_input: 用户输入

    Returns:
        AI 回复
    """
    chatbot = ChatBot()
    return chatbot.chat(user_input)


if __name__ == "__main__":
    user_input = input("You: ")
    response = main(user_input)
    print(f"Bot: {response}")