# test/unit/test_hooks.py
import pytest
from src.hooks.middleware import MiddlewareHooks


def test_hooks_print_output(capsys):
    """验证每个 hook 触发时打印日志"""
    hooks = MiddlewareHooks()

    hooks.on_before_agent()
    captured = capsys.readouterr()
    assert "[Hook] before_agent triggered" in captured.out

    hooks.on_before_model()
    captured = capsys.readouterr()
    assert "[Hook] before_model triggered" in captured.out

    hooks.on_after_model()
    captured = capsys.readouterr()
    assert "[Hook] after_model triggered" in captured.out

    hooks.on_after_agent()
    captured = capsys.readouterr()
    assert "[Hook] after_agent triggered" in captured.out

    hooks.on_wrap_model_call()
    captured = capsys.readouterr()
    assert "[Hook] wrap_model_call triggered" in captured.out

    hooks.on_wrap_tool_call()
    captured = capsys.readouterr()
    assert "[Hook] wrap_tool_call triggered" in captured.out