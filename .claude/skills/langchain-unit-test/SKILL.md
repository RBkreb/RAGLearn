---
name: langchain-unit-test
description: |
  Write LangChain unit tests with fake chat models and in-memory checkpointer. Use this skill whenever:
  - User asks to write unit tests for a LangChain agent, chain, or component
  - User mentions testing LangChain code in isolation without real API calls
  - User describes a LangChain component that needs test coverage
  - User asks to add tests for an agent, tool, memory, or chain
  - User says "test this LangChain component" or "mock the LLM for testing"
  - User asks how to test LangChain code without API keys or external calls
  This skill provides LangChain's official unit testing patterns with GenericFakeChatModel and InMemorySaver.
version: 1.0.0
---

# LangChain Unit Test Skill

Write fast, deterministic unit tests for LangChain components using fake chat models and in-memory persistence.

## Core Principle

**Unit tests exercise small, deterministic pieces in isolation.** Replace the real LLM with an in-memory fake so tests are fast, free, and repeatable without API keys.

---

## 1. Fake Chat Model (GenericFakeChatModel)

LangChain provides `GenericFakeChatModel` for mocking text responses. It accepts an iterator of responses and returns one per invocation.

```python
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolCall

# Mock text responses
model = GenericFakeChatModel(messages=iter([
    "Hello! How can I help you?",
    "The weather is sunny today."
]))

# Mock tool calls
model = GenericFakeChatModel(messages=iter([
    AIMessage(content="", tool_calls=[
        ToolCall(name="foo", args={"bar": "baz"}, id="call_1")
    ])
]))

# Streaming mode also supported
model = GenericFakeChatModel(messages=iter(["streamed ", "response"]))
```

**Key behaviors:**
- Each `.invoke()` returns the next item in the iterator
- Strings are auto-wrapped in `AIMessage(content=...)`
- Tool calls must be explicit `AIMessage` objects with `tool_calls`

---

## 2. In-Memory Checkpointer

For testing stateful agents (multiple turns), use `InMemorySaver`:

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

agent = create_agent(
    model,
    tools=[],
    checkpointer=checkpointer
)

# First turn
result = agent.invoke(
    {"messages": [HumanMessage(content="I live in Sydney, Australia")]},
    config={"configurable": {"thread_id": "session-1"}}
)

# Second turn: state persisted from first turn
result = agent.invoke(
    {"messages": [HumanMessage(content="What's my local time?")]},
    config={"configurable": {"thread_id": "session-1"}}
)
```

---

## 3. Test Structure

Organize tests following this pattern:

```python
# tests/unit/test_my_agent.py
import pytest
from unittest.mock import Mock
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolCall
from my_agent import create_agent

class TestMyAgent:
    """Unit tests for MyAgent."""

    def test_handles_simple_query(self):
        """Agent returns greeting response."""
        model = GenericFakeChatModel(messages=iter([
            "Hello! How can I assist you today?"
        ]))
        agent = create_agent(model, tools=[])

        result = agent.invoke({
            "messages": [HumanMessage(content="Hi")]
        })

        assert isinstance(result["messages"][-1], AIMessage)
        assert "Hello" in result["messages"][-1].content

    def test_calls_correct_tool(self):
        """Agent selects the weather tool when asked about weather."""
        model = GenericFakeChatModel(messages=iter([
            AIMessage(content="", tool_calls=[
                ToolCall(name="get_weather", args={"city": "SF"}, id="call_1")
            ])
        ]))
        agent = create_agent(model, tools=[get_weather])

        result = agent.invoke({
            "messages": [HumanMessage(content="What's the weather in SF?")]
        })

        # Extract tool calls from messages
        tool_calls = [
            tc for msg in result["messages"]
            if hasattr(msg, "tool_calls") and msg.tool_calls
            for tc in msg.tool_calls
        ]
        assert any(tc["name"] == "get_weather" for tc in tool_calls)

    def test_maintains_conversation_state(self):
        """Agent remembers context across turns."""
        checkpointer = InMemorySaver()
        model = GenericFakeChatModel(messages=iter([
            "Got it, Sydney.",
            "It's 10:00 AM in Sydney."  # Second turn response
        ]))
        agent = create_agent(model, tools=[], checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "test-thread"}}

        # First turn
        agent.invoke(
            {"messages": [HumanMessage(content="I live in Sydney, Australia")]},
            config=config
        )

        # Second turn - should have context
        result = agent.invoke(
            {"messages": [HumanMessage(content="What's my local time?")]},
            config=config
        )

        assert "Sydney" in result["messages"][-1].content
```

---

## 4. Testing Specific Components

### Testing Chains

```python
def test_llm_chain_produces_output():
    """LLMChain transforms input to output correctly."""
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate

    model = GenericFakeChatModel(messages=iter(["The capital of France is Paris."]))
    chain = LLMChain(
        llm=model,
        prompt=PromptTemplate.from_template("What is the capital of {country}?")
    )

    result = chain.invoke({"country": "France"})

    assert "Paris" in result["text"]
```

### Testing Tools in Isolation

```python
def test_tool_returns_formatted_result():
    """Tool correctly formats search results."""
    from my_tools import search_documents

    # Tool doesn't need LLM - test directly
    result = search_documents.invoke({"query": "test", "top_k": 3})

    assert "test" in result
    assert len(result.split("\n")) <= 3
```

### Testing Memory

```python
def test_memory_saves_and_loads_context(self):
    """ConversationBufferMemory persists context correctly."""
    from langchain.memory import ConversationBufferMemory
    from langchain_core.messages import AIMessage, HumanMessage

    memory = ConversationBufferMemory()
    memory.save_context(
        {"input": "My name is Alice"},
        {"output": "Hello Alice!"}
    )

    variables = memory.load_memory_variables({})

    assert "Alice" in variables["history"]
    assert "Hello" in variables["history"]
```

### Testing Retrievers

```python
def test_retriever_returns_relevant_docs(self):
    """Retriever fetches documents matching query."""
    from my_retriever import create_retriever
    from langchain_core.documents import Document

    # Mock vector store
    mock_vectorstore = Mock()
    mock_vectorstore.similarity_search.return_value = [
        Document(page_content="Python is a great language", metadata={"source": "python.txt"})
    ]

    retriever = create_retriever(mock_vectorstore)
    results = retriever.invoke("programming language")

    assert len(results) == 1
    assert "Python" in results[0].page_content
```

---

## 5. Mocking Best Practices

| Component | Mocking Strategy |
|-----------|------------------|
| Chat Model | `GenericFakeChatModel` with scripted responses |
| Checkpointer | `InMemorySaver` from `langgraph.checkpoint.memory` |
| Tools | Mock the tool function directly, or use `UntypedObject` |
| Vector Store | Mock `.similarity_search()` return value |
| External APIs | Use `pytest-mock` or `unittest.mock.Mock` |

**Never use real API keys in unit tests.** If testing requires real API calls, it's an integration test — mark with `@pytest.mark.integration`.

---

## 6. Test File Organization

```
tests/
├── unit/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_chains.py
│   ├── test_tools.py
│   ├── test_memory.py
│   └── test_retrievers.py
└── integration/  # Separate, marked with @pytest.mark.integration
```

---

## 7. Running Unit Tests

```bash
# Run all unit tests
./venv/Scripts/python.exe -m pytest tests/unit/ -v

# Run specific test file
./venv/Scripts/python.exe -m pytest tests/unit/test_agents.py -v

# Run with coverage
./venv/Scripts/python.exe -m pytest tests/unit/ --cov=src --cov-report=term-missing

# Exclude integration tests (recommended in CI)
./venv/Scripts/python.exe -m pytest -m "not integration"
```

---

## 8. Key Points to Remember

1. **Test in isolation** — no real LLM calls, no network
2. **Use `GenericFakeChatModel`** — scripts exact responses for deterministic tests
3. **Use `InMemorySaver`** — tests multi-turn conversations without persistence
4. **Assert on structure** — check message types, tool call names, not exact text
5. **One behavior per test** — keeps tests focused and debuggable
6. **Mock external dependencies** — vector stores, APIs, databases