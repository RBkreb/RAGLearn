---
name: langchain-integration-test
description: |
  Write LangChain integration tests with real LLM APIs, pytest markers, VCR cassette recording, and cost management. Use this skill whenever:
  - User asks to write integration tests for a LangChain agent or component
  - User mentions testing LangChain with real API calls (OpenAI, Anthropic, etc.)
  - User describes adding integration tests to CI/CD pipeline
  - User asks about recording/replaying HTTP calls (VCR cassettes)
  - User wants to test tool calling with real models
  - User asks about API key management for tests
  - User says "integration test" or "end-to-end test" for LangChain
  This skill follows LangChain's official integration testing patterns.
version: 1.0.0
---

# LangChain Integration Test Skill

Write integration tests that verify LangChain agents work correctly with real LLM APIs and external services.

## Core Principle

**Integration tests verify components work together with real APIs.** Unlike unit tests that use fakes, integration tests make actual network calls. Because LLM responses are nondeterministic, you must assert on structure, not exact content.

---

## 1. Separate Unit and Integration Tests

Keep integration tests **separate** from unit tests. Run unit tests on every change; run integration tests only in CI or pre-deploy.

### pytest Markers

```python
import pytest

@pytest.mark.integration
def test_agent_with_real_model():
    """Integration test that calls real LLM API."""
    agent = create_agent("claude-sonnet-4-6", tools=[get_weather])
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in SF?")]
    })
    assert len(result["messages"]) > 1
```

### Configure pytest

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "integration: tests that call real LLM APIs"
]
addopts = "-m 'not integration'"
```

Run integration tests explicitly:
```bash
pytest -m integration
```

---

## 2. API Key Management

Load credentials from environment variables — never hardcode keys.

### conftest.py Pattern

```python
# tests/conftest.py
import os
import pytest
from dotenv import load_dotenv

load_dotenv()  # Load .env for local dev

@pytest.fixture(autouse=True)
def check_api_keys():
    """Skip integration tests if API keys are not available."""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
```

### .env File (add to .gitignore)

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### CI Secrets

Inject secrets through your CI provider's secrets management (GitHub Actions secrets, etc.).

---

## 3. Assert on Structure, Not Content

LLM responses vary between runs. **Never assert on exact output strings.**

### Good Assertions

```python
def test_agent_calls_weather_tool():
    """Verify agent calls the correct tool."""
    agent = create_agent("claude-sonnet-4-6", tools=[get_weather])
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in SF?")]
    })

    # Extract tool calls
    tool_calls = [
        tc
        for msg in result["messages"]
        if hasattr(msg, "tool_calls") and msg.tool_calls
        for tc in msg.tool_calls
    ]

    # Assert on structure, not exact content
    assert any(tc["name"] == "get_weather" for tc in tool_calls)
    assert isinstance(result["messages"][-1], AIMessage)
    assert len(result["messages"][-1].content) > 0
```

### Bad Assertions (Don't Do This)

```python
# WRONG - Will fail randomly due to LLM nondeterminism
assert result == "The weather in San Francisco is 72 degrees."

# WRONG - Exact string matching is fragile
assert "72 degrees" in result["messages"][-1].content
```

---

## 4. Reduce Cost and Latency

Integration tests incur real API costs. Follow these practices:

### Use Smaller Models for Testing

```python
# Use lightweight models for tests that only verify structure
agent = create_agent(
    "gemini-3.1-flash-lite-preview",  # Cheaper model
    tools=[get_weather],
    model_kwargs={"max_tokens": 256}  # Cap response length
)
```

### Best Practices

| Practice | Why |
|----------|-----|
| Use smaller models | `gemini-3.1-flash-lite-preview` for structure-only tests |
| Set `max_tokens` | Avoid long, expensive completions |
| Test one behavior per test | Limit scope, reduce cost |
| Run selectively | Use markers to run only in CI, not on every save |

---

## 5. Record and Replay HTTP Calls (VCR)

For frequent CI runs, record HTTP interactions and replay them without real API calls.

### Setup

```bash
pip install pytest-recording vcrpy
```

### conftest.py Configuration

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def vcr_config():
    return {
        "filter_headers": [
            ("authorization", "XXXX"),
            ("x-api-key", "XXXX"),
        ],
        "filter_query_parameters": [
            ("api_key", "XXXX"),
            ("key", "XXXX"),
        ],
    }
```

### Configure pytest

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "vcr: record/replay HTTP via VCR"
]
addopts = "--record-mode=once"
```

### Use VCR Marker

```python
@pytest.mark.vcr()
def test_agent_trajectory():
    """Test with recorded HTTP cassettes."""
    agent = create_agent("claude-sonnet-4-6", tools=[get_weather])
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in SF?")]
    })

    # Verify tool was called
    assert any(
        tc["name"] == "get_weather"
        for msg in result["messages"]
        if hasattr(msg, "tool_calls") and msg.tool_calls
        for tc in msg.tool_calls
    )
```

### How VCR Works

1. **First run**: Makes real API calls, records HTTP to `tests/cassettes/`
2. **Subsequent runs**: Replays recorded responses (no API calls)
3. **When prompts change**: Delete cassette files and rerun to record fresh

---

## 6. Test Structure

```python
# tests/integration/test_agent.py
import pytest
from langchain_core.messages import HumanMessage, AIMessage

@pytest.mark.integration
class TestAgentIntegration:
    """Integration tests for agent with real APIs."""

    def test_agent_completes_basic_task(self):
        """Agent successfully completes a simple task."""
        agent = create_agent("claude-sonnet-4-6", tools=[])

        result = agent.invoke({
            "messages": [HumanMessage(content="Say 'hello' in Chinese")]
        })

        # Structure assertions
        assert len(result["messages"]) >= 2
        assert isinstance(result["messages"][-1], AIMessage)
        assert len(result["messages"][-1].content) > 0

    def test_agent_calls_tool(self):
        """Agent correctly invokes a tool."""
        agent = create_agent("claude-sonnet-4-6", tools=[get_weather])

        result = agent.invoke({
            "messages": [HumanMessage(content="What's the weather in Tokyo?")]
        })

        # Verify tool was selected
        tool_calls = [
            tc
            for msg in result["messages"]
            if hasattr(msg, "tool_calls") and msg.tool_calls
            for tc in msg.tool_calls
        ]
        assert any(tc["name"] == "get_weather" for tc in tool_calls)
```

---

## 7. Test File Organization

```
tests/
├── unit/                    # Fast, no API calls
│   ├── test_agents.py
│   └── test_chains.py
├── integration/            # Slow, real API calls
│   ├── conftest.py         # Shared fixtures, API key checks
│   ├── cassettes/          # VCR recordings (auto-generated)
│   ├── test_agents.py
│   └── test_chains.py
└── conftest.py             # Root-level shared fixtures
```

---

## 8. Running Tests

```bash
# Run all unit tests (fast, no API)
./venv/Scripts/python.exe -m pytest tests/unit/ -v

# Run all integration tests (slow, real API)
./venv/Scripts/python.exe -m pytest -m integration -v

# Run with VCR (record or replay)
./venv/Scripts/python.exe -m pytest -m vcr --record-mode=once

# Run specific test
./venv/Scripts/python.exe -m pytest tests/integration/test_agents.py::TestAgentIntegration::test_agent_calls_tool -v

# Run with coverage
./venv/Scripts/python.exe -m pytest tests/ --cov=src --cov-report=term-missing
```

---

## 9. CI Integration

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  unit-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run unit tests
        run: pytest tests/unit/ -m "not integration"

  integration-test:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4
      - name: Run integration tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: pytest -m integration -v
```

---

## 10. Key Points to Remember

1. **Separate from unit tests** — use pytest markers
2. **Manage API keys via environment** — never hardcode
3. **Assert on structure** — not exact text (LLMs are nondeterministic)
4. **Use smaller models** — for tests that only verify tool calling
5. **Consider VCR** — for frequent CI runs to reduce cost
6. **Run selectively** — only in CI or pre-deploy, not on every save