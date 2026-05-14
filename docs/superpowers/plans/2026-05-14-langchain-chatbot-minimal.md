# LangChain 对话机器人最小实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立包含所有 LangChain middleware hooks（占位符）和占位符 tool 的最小对话机器人，实现单轮对话功能

**Architecture:** 使用 LangChain 的 `BaseCallbackHandler` 实现 6 个 middleware hooks，ChatBot 类封装对话逻辑，PlaceholderTool 定义但暂不绑定

**Tech Stack:** langchain-openai, langchain-core

---

## File Structure

```
src/
├── __init__.py
├── chatbot.py          # ChatBot 类，包含 6 个 hook 方法
├── tools/
│   ├── __init__.py
│   └── placeholder.py # PlaceholderTool
├── hooks/
│   ├── __init__.py
│   └── middleware.py  # MiddlewareHooks
└── main.py            # 单轮对话入口

test/
└── unit/
    └── test_chatbot.py
```

---


## Task 1: MiddlewareHooks 占位符实现

**Files:**
- Create: `src/hooks/__init__.py`
- Create: `src/hooks/middleware.py`
- Test: `test/unit/test_hooks.py`

- [ ] **Step 1: 编写 MiddlewareHooks 测试**

```python
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
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd e:/Uagent && ./venv/Scripts/pytest.exe test/unit/test_hooks.py -v
```
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 创建 src/hooks/__init__.py**

```python
# src/hooks/__init__.py
from .middleware import MiddlewareHooks

__all__ = ["MiddlewareHooks"]
```

- [ ] **Step 4: 创建 src/hooks/middleware.py**

```python
# src/hooks/middleware.py
"""LangChain Middleware Hooks - 占位符实现"""

from langchain_core.callbacks import BaseCallbackHandler


class MiddlewareHooks(BaseCallbackHandler):
    """包含所有 LangChain hooks 的占位符实现，每个 hook 触发时打印日志"""

    def on_before_agent(self, **kwargs) -> None:
        print("[Hook] before_agent triggered")

    def on_before_model(self, **kwargs) -> None:
        print("[Hook] before_model triggered")

    def on_after_model(self, **kwargs) -> None:
        print("[Hook] after_model triggered")

    def on_after_agent(self, **kwargs) -> None:
        print("[Hook] after_agent triggered")

    def on_wrap_model_call(self, **kwargs) -> None:
        print("[Hook] wrap_model_call triggered")

    def on_wrap_tool_call(self, **kwargs) -> None:
        print("[Hook] wrap_tool_call triggered")
```

- [ ] **Step 5: 运行测试验证通过**

```bash
cd e:/Uagent && ./venv/Scripts/pytest.exe test/unit/test_hooks.py -v
```
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add src/hooks/__init__.py src/hooks/middleware.py test/unit/test_hooks.py requirements.txt
git commit -m "feat: add MiddlewareHooks with 6 placeholder hooks"
```

---

## Task 2: PlaceholderTool 定义

**Files:**
- Create: `src/tools/__init__.py`
- Create: `src/tools/placeholder.py`
- Test: `test/unit/test_placeholder_tool.py`

- [ ] **Step 1: 编写 PlaceholderTool 测试**

```python
# test/unit/test_placeholder_tool.py
import pytest
from src.tools.placeholder import placeholder_tool


def test_placeholder_tool_returns_input():
    """验证占位符工具返回格式化后的输入"""
    result = placeholder_tool.invoke("hello")
    assert result == "Placeholder tool received: hello"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd e:/Uagent && ./venv/Scripts/pytest.exe test/unit/test_placeholder_tool.py -v
```
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 创建 src/tools/__init__.py**

```python
# src/tools/__init__.py
from .placeholder import placeholder_tool

__all__ = ["placeholder_tool"]
```

- [ ] **Step 4: 创建 src/tools/placeholder.py**

```python
# src/tools/placeholder.py
"""Placeholder Tool - 暂不绑定到 agent"""

from langchain_core.tools import tool


@tool
def placeholder_tool(input: str) -> str:
    """占位符工具，用于后续扩展。

    Args:
        input: 用户输入字符串

    Returns:
        格式化后的响应字符串
    """
    return f"Placeholder tool received: {input}"
```

- [ ] **Step 5: 运行测试验证通过**

```bash
cd e:/Uagent && ./venv/Scripts/pytest.exe test/unit/test_placeholder_tool.py -v
```
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add src/tools/__init__.py src/tools/placeholder.py test/unit/test_placeholder_tool.py
git commit -m "feat: add PlaceholderTool"
```

---

## Task 3: ChatBot 类实现

**Files:**
- Create: `src/__init__.py`
- Create: `src/chatbot.py`
- Test: `test/unit/test_chatbot.py`

- [ ] **Step 1: 编写 ChatBot 测试**

```python
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
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd e:/Uagent && ./venv/Scripts/pytest.exe test/unit/test_chatbot.py -v
```
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 创建 src/__init__.py**

```python
# src/__init__.py
from .chatbot import ChatBot
from .tools import placeholder_tool
from .hooks import MiddlewareHooks

__all__ = ["ChatBot", "placeholder_tool", "MiddlewareHooks"]
```

- [ ] **Step 4: 创建 src/chatbot.py**

```python
# src/chatbot.py
"""LangChain 对话机器人 - 最小实现"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from .hooks import MiddlewareHooks


class ChatBot:
    """包含所有 middleware hooks 的对话机器人"""

    def __init__(
        self,
        model_name: str = "gpt-4",
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

        messages = [HumanMessage(content=user_input)]
        response = self._llm.invoke(messages)

        self._hooks.on_after_model(response)
        self._hooks.on_after_agent()

        return response.content
```

- [ ] **Step 5: 运行测试验证通过**

```bash
cd e:/Uagent && ./venv/Scripts/pytest.exe test/unit/test_chatbot.py -v
```
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add src/__init__.py src/chatbot.py test/unit/test_chatbot.py
git commit -m "feat: add ChatBot class with middleware hooks"
```

---

## Task 4: Main 入口实现

**Files:**
- Create: `src/main.py`
- Test: `test/unit/test_main.py`

- [ ] **Step 1: 编写 main 测试**

```python
# test/unit/test_main.py
import pytest
from unittest.mock import patch


def test_main_single_turn(capsys):
    """验证单轮对话执行"""
    with patch("src.main.ChatBot") as mock_chatbot:
        mock_instance = mock_chatbot.return_value
        mock_instance.chat.return_value = "Test response"

        from src.main import main
        result = main("Hello")

        assert result == "Test response"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd e:/Uagent && ./venv/Scripts/pytest.exe test/unit/test_main.py -v
```
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 创建 src/main.py**

```python
# src/main.py
"""LangChain 对话机器人入口"""

from .chatbot import ChatBot


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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd e:/Uagent && ./venv/Scripts/pytest.exe test/unit/test_main.py -v
```
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/main.py test/unit/test_main.py
git commit -m "feat: add main entry point"
```

---

## Task 5: 手动验证

- [ ] **Step 1: 运行完整程序**

```bash
cd e:/Uagent && ./venv/Scripts/python.exe -c "
from src.main import main
print(main('Hello'))
"
```

Expected output:
```
[Hook] before_agent triggered
[Hook] before_model triggered
[Hook] after_model triggered
[Hook] after_agent triggered
Bot: <AI回复>
```

- [ ] **Step 6: 提交最终版本**

```bash
git add -A
git commit -m "feat: complete minimal LangChain chatbot with all middleware hooks"
```

---

## Verification Summary

1. **单元测试**: `pytest test/unit/ -v` 全部通过
2. **Hook 输出**: 运行程序时可见 4 个 hook 的日志输出
3. **单轮对话**: 能够接收输入并返回 AI 回复