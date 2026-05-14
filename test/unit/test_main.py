# test/unit/test_main.py
import pytest
from unittest.mock import patch


def test_main_single_turn():
    """验证单轮对话执行"""
    with patch("src.main.ChatBot") as mock_chatbot:
        mock_instance = mock_chatbot.return_value
        mock_instance.chat.return_value = "Test response"

        from src.main import main
        result = main("Hello")

        assert result == "Test response"