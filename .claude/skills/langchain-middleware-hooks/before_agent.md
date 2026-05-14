---
name: langchain-before-agent-hook
description: Use when implementing @before_agent middleware hook in LangChain v1. Triggers before the agent starts execution - ideal for authentication, authorization, rate limiting, request validation, or blocking inappropriate content before any processing begins.
---

# LangChain `@before_agent` Hook

## When to Use

The `@before_agent` hook fires **once per agent invocation**, before any agent logic executes. Use it for:

- **Authentication/Authorization** - Verify user identity or permissions before processing
- **Rate Limiting** - Block requests that exceed usage limits
- **Input Validation** - Validate request format, required fields, or content policies
- **Content Filtering** - Scan for inappropriate keywords or prompt injection attempts
- **Request Logging** - Audit who is making what request and when

## Purpose

Prevents unauthorized or invalid requests from consuming resources. Acts as a gatekeeper at the entry point of agent execution.

## Return Value

`dict[str, Any] | None`:
- Return `None` to continue execution normally
- Return a dict to update state or short-circuit via `jump_to`
- Common short-circuit pattern: `{"messages": [...], "jump_to": "end"}` to return early with a custom message

## Signature

```python
from langchain.agents.middleware import before_agent, AgentState
from langgraph.runtime import Runtime
from typing import Any

@before_agent(can_jump_to=["end"])
def my_hook(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    ...
```

## Example: Content Filter Middleware

```python
from typing import Any
from langchain.agents.middleware import before_agent, AgentState
from langgraph.runtime import Runtime

BANNED_KEYWORDS = ["hack", "exploit", "malware", "inject"]

@before_agent(can_jump_to=["end"])
def content_filter(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Block requests containing banned keywords before agent processes them."""

    if not state.get("messages"):
        return None

    first_message = state["messages"][0]

    # Only check human messages
    if not hasattr(first_message, "content") or first_message.type != "human":
        return None

    content = first_message.content.lower()

    for keyword in BANNED_KEYWORDS:
        if keyword in content:
            return {
                "messages": [{
                    "type": "ai",
                    "content": "I cannot process requests containing inappropriate content."
                }],
                "jump_to": "end"
            }

    return None
```

## Example: Rate Limiter

```python
from typing import Any
from datetime import datetime, timedelta
from langchain.agents.middleware import before_agent, AgentState
from langgraph.runtime import Runtime

# In-memory rate limiting (use Redis in production)
_request_counts: dict[str, list[datetime]] = {}
RATE_LIMIT = 10  # requests
WINDOW = timedelta(minutes=1)

@before_agent(can_jump_to=["end"])
def rate_limiter(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Limit requests per user within a time window."""

    user_id = state.get("user_id", "anonymous")
    now = datetime.now()

    # Clean old requests
    if user_id in _request_counts:
        _request_counts[user_id] = [
            ts for ts in _request_counts[user_id]
            if now - ts < WINDOW
        ]
    else:
        _request_counts[user_id] = []

    if len(_request_counts[user_id]) >= RATE_LIMIT:
        return {
            "messages": [{
                "type": "ai",
                "content": "Rate limit exceeded. Please try again later."
            }],
            "jump_to": "end"
        }

    _request_counts[user_id].append(now)
    return None
```

## Execution Position

```
Agent Execution Flow:
┌─────────────────────────────────────────────────────────┐
│  @before_agent  ──►  [Agent Loop]  ──►  @after_agent    │
│       │                    │                    │       │
│   Entry gate          Model calls           Exit gate    │
└─────────────────────────────────────────────────────────┘
```

## Notes

- Runs **once per agent invocation**, not per step in the agent loop
- `can_jump_to=["end"]` allows short-circuiting to the end node
- State updates returned are merged via graph reducers
- Multiple `@before_agent` hooks run in declaration order (first to last)