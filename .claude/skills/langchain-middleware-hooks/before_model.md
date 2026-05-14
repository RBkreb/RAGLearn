---
name: langchain-before-model-hook
description: Use when implementing @before_model middleware hook in LangChain v1. Triggers before each model call inside the agent loop - ideal for prompt injection prevention, dynamic context injection, intent-based prompt modification, or input transformation before the LLM processes the request.
---

# LangChain `@before_model` Hook

## When to Use

The `@before_model` hook fires **before each model call** inside the agent loop (runs multiple times per agent invocation). Use it for:

- **Dynamic Prompt Injection** - Add context based on conversation state or intent
- **System Prompt Modification** - Update system instructions based on user intent
- **Message Transformation** - Transform, truncate, or enrich messages before LLM sees them
- **Token Budget Management** - Truncate messages approaching context limits
- **Intent-Based Routing** - Detect user intent and inject relevant tool descriptions

## Purpose

Modifies what the LLM sees on each model call. Unlike `@before_agent` which runs once, this runs multiple times as the agent loops through model calls.

## Return Value

`dict[str, Any] | None`:
- Return `None` to continue with original messages
- Return a dict to update state (messages are replaced/augmented)
- Use `jump_to` to short-circuit to different nodes ("end", "tools", "model")

## Signature

```python
from langchain.agents.middleware import before_model, AgentState
from langgraph.runtime import Runtime
from typing import Any

@before_model(can_jump_to=["end"])
def my_hook(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    ...
```

## Example: Intent-Based Context Injection

```python
from typing import Any
from langchain.agents.middleware import before_model, AgentState
from langgraph.runtime import Runtime
from langchain.messages import SystemMessage

INTENT_PROMPTS = {
    "math": "You are helping with mathematical calculations. Show all work.",
    "code": "You are a coding assistant. Always provide type hints and docstrings.",
    "general": "You are a helpful conversational assistant."
}

@before_model(can_jump_to=["end"])
def intent_context_injector(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Inject intent-specific context based on detected intent."""

    if not state.get("messages"):
        return None

    # Detect intent from first user message
    first_msg = state["messages"][0]
    if not hasattr(first_msg, "content"):
        return None

    content = first_msg.content.lower()

    if "calculate" in content or "math" in content or "=" in content:
        intent = "math"
    elif "code" in content or "function" in content or "def " in content:
        intent = "code"
    else:
        intent = "general"

    # Prepend system message for this intent
    new_messages = [SystemMessage(content=INTENT_PROMPTS[intent])] + state["messages"]

    return {"messages": new_messages}
```

## Example: Conversation Length Guard

```python
from typing import Any
from langchain.agents.middleware import before_model, AgentState
from langgraph.runtime import Runtime
from langchain.messages import AIMessage

MAX_MESSAGES = 50

@before_model(can_jump_to=["end"])
def message_limit_guard(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Prevent excessive message accumulation in conversation."""

    message_count = len(state.get("messages", []))

    if message_count >= MAX_MESSAGES:
        return {
            "messages": [AIMessage(
                content="Conversation limit reached. Please start a new session."
            )],
            "jump_to": "end"
        }

    return None
```

## Example: Dynamic Tool Selection

```python
from typing import Any
from langchain.agents.middleware import before_model, AgentState
from langgraph.runtime import Runtime
from langchain.messages import SystemMessage

AVAILABLE_TOOLS = {
    "search": ["search", "find", "look up", "google"],
    "calculator": ["calculate", "compute", "math", "+", "-", "*", "/"],
    "weather": ["weather", "temperature", "forecast"]
}

def get_tools_for_intent(content: str) -> list[str]:
    """Determine which tools to enable based on user query."""
    content_lower = content.lower()
    enabled = []
    for tool, keywords in AVAILABLE_TOOLS.items():
        if any(kw in content_lower for kw in keywords):
            enabled.append(tool)
    return enabled if enabled else ["search"]  # default

@before_model(can_jump_to=["end"])
def dynamic_tool_injector(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Inject relevant tools based on detected user intent."""

    if not state.get("messages"):
        return None

    first_msg = state["messages"][0]
    if not hasattr(first_msg, "content"):
        return None

    enabled_tools = get_tools_for_intent(first_msg.content)
    tool_list = ", ".join(enabled_tools)

    system_msg = SystemMessage(
        content=f"You have access to these tools: {tool_list}. Use them as needed."
    )

    return {"messages": [system_msg] + state["messages"]}
```

## Execution Position

```
Agent Loop (repeats until done):
┌─────────────────────────────────────────────────────────┐
│  @before_model  ──►  Model Call  ──►  @after_model     │
│         │                 │                  │           │
│    Pre-LLM prep    LLM inference      Post-LLM proc    │
└─────────────────────────────────────────────────────────┘
```

## Notes

- Runs **multiple times per agent invocation** - once before each model call
- State updates are merged between hooks
- Can modify messages array before LLM sees them
- `jump_to` allows branching to different graph nodes
- Multiple `@before_model` hooks run in declaration order