# test/unit/test_chatbot.py
import pytest
from unittest.mock import patch, MagicMock
from src.chatbot import ChatBot


def test_chatbot_initialization():
    """验证 ChatBot 正确初始化"""
    chatbot = ChatBot()
    assert chatbot.model_name == "gpt-4"
    assert chatbot.base_url == "http://127.0.0.1:1234"


@patch("src.chatbot.ChatOpenAI")
def test_chat_single_round(mock_chatopenai):
    """验证单轮对话功能"""
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = MagicMock(content="Hello from bot")
    mock_chatopenai.return_value = mock_instance

    chatbot = ChatBot()
    response = chatbot.chat("Hi")

    assert response == "Hello from bot"
    mock_instance.invoke.assert_called_once()