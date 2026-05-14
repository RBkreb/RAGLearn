---
name: langchain-after-model-hook
description: Use when implementing @after_model middleware hook in LangChain v1. Triggers after each model response inside the agent loop - ideal for response logging, output filtering, token counting, content moderation, or modifying the model's output before it propagates through the pipeline.
---

# LangChain `@after_model` Hook

## When to Use

The `@after_model` hook fires **after each model response** inside the agent loop (runs multiple times per agent invocation). Use it for:

- **Response Logging** - Log all LLM outputs for debugging or analytics
- **Content Filtering** - Check response for disallowed content or PII
- **Token Counting** - Track input/output tokens for usage monitoring
- **Output Transformation** - Modify or post-process model responses
- **State Updates** - Update counters, flags, or derived state based on response

## Purpose

Inspects and optionally modifies the LLM's output before it continues through the agent pipeline. Allows mid-loop course correction.

## Return Value

`dict[str, Any] | None`:
- Return `None` for no changes
- Return a dict to merge state updates via graph reducers
- Does NOT support `jump_to` - only state modifications

## Signature

```python
from langchain.agents.middleware import after_model, AgentState
from langgraph.runtime import Runtime
from typing import Any

@after_model
def my_hook(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    ...
```

## Example: Response Logger

```python
from typing import Any
from datetime import datetime
from langchain.agents.middleware import after_model, AgentState
from langgraph.runtime import Runtime

@after_model
def response_logger(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Log all model responses for debugging."""

    if not state.get("messages"):
        return None

    last_message = state["messages"][-1]

    if hasattr(last_message, "content"):
        print(f"[{datetime.now().isoformat()}] Model response: {last_message.content[:100]}...")

    return None
```

## Example: Token Usage Tracker

```python
from typing import Any
from langchain.agents.middleware import after_model, AgentState
from langgraph.runtime import Runtime

# Simple in-memory tracker (use external storage in production)
_token_counts: dict[str, dict[str, int]] = {}

@after_model
def track_tokens(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Track token usage per conversation."""

    conversation_id = state.get("conversation_id", "default")

    if conversation_id not in _token_counts:
        _token_counts[conversation_id] = {"input": 0, "output": 0, "total": 0}

    # Assume token counting happens elsewhere or estimate
    # This is a simplified example
    last_message = state["messages"][-1] if state.get("messages") else None

    if last_message and hasattr(last_message, "content"):
        estimated_tokens = len(last_message.content) // 4  # rough estimate

        _token_counts[conversation_id]["output"] += estimated_tokens
        _token_counts[conversation_id]["total"] += estimated_tokens

    return {
        "token_usage": {
            "input_tokens": _token_counts[conversation_id]["input"],
            "output_tokens": _token_counts[conversation_id]["output"],
            "total_tokens": _token_counts[conversation_id]["total"]
        }
    }
```

## Example: Output Content Filter

```python
from typing import Any
from langchain.agents.middleware import after_model, AgentState
from langgraph.runtime import Runtime

BLOCKED_PATTERNS = ["ssn:", "password:", "api_key:", "secret:"]
REPLACEMENT = "[REDACTED]"

@after_model
def content_sanitizer(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Sanitize sensitive data from model responses."""

    if not state.get("messages"):
        return None

    last_message = state["messages"][-1]

    if not hasattr(last_message, "content"):
        return None

    content = last_message.content

    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in content.lower():
            # Mark the message as needing review
            return {
                "messages": [{
                    **last_message.dict() if hasattr(last_message, 'dict') else {"type": last_message.type, "content": content},
                    "content": content.replace(pattern, REPLACEMENT),
                    "needs_review": True
                }]
            }

    return None
```

## Example: Response Categorizer

```python
from typing import Any
from langchain.agents.middleware import after_model, AgentState
from langgraph.runtime import Runtime

RESPONSE_CATEGORIES = ["informative", "actionable", "clarifying", "error"]

@after_model
def categorize_response(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Categorize the model's response for analysis."""

    if not state.get("messages"):
        return None

    last_message = state["messages"][-1]

    if not hasattr(last_message, "content"):
        return None

    content = last_message.content.lower()

    # Simple keyword-based categorization
    if "?" in content:
        category = "clarifying"
    elif any(word in content for word in ["will", "can", "could", "should"]):
        category = "actionable"
    elif any(word in content for word in ["error", "failed", "cannot"]):
        category = "error"
    else:
        category = "informative"

    return {"last_response_category": category}
```

## Execution Position

```
Agent Loop (repeats until done):
┌─────────────────────────────────────────────────────────┐
│  @before_model  ──►  Model Call  ──►  @after_model     │
│         │                 │                  │           │
│    Pre-LLM prep    LLM inference      Post-LLM proc     │
└─────────────────────────────────────────────────────────┘
```

## Notes

- Runs **multiple times per agent invocation** - after each model call
- Does NOT support `jump_to` - only state modifications
- Returned dict is merged into state via graph reducers
- Last message in `state["messages"]` is the model response
- Multiple `@after_model` hooks run in **reverse order** (last to first)
- Useful for building up state across multiple model calls in a loop