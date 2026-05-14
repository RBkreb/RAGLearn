---
name: langchain-after-agent-hook
description: Use when implementing @after_agent middleware hook in LangChain v1. Triggers once after the agent completes execution - ideal for final response validation, safety checks on complete outputs, cleanup operations, or logging final results to external systems.
---

# LangChain `@after_agent` Hook

## When to Use

The `@after_agent` hook fires **once after the agent completes** (after the agent loop exits). Use it for:

- **Final Response Validation** - Safety check on the complete response
- **Output Logging** - Log final results to external systems (databases, analytics)
- **Cleanup Operations** - Release resources, close connections
- **Post-Processing** - Transform the final output before returning
- **Session Summary** - Generate or update conversation summaries

## Purpose

Acts as a final checkpoint after agent execution completes. Unlike `@after_model` which runs in the loop, this runs once at the end.

## Return Value

`dict[str, Any] | None`:
- Return `None` for no changes
- Return a dict to modify final state before returning to user
- Supports `can_jump_to` for additional processing nodes

## Signature

```python
from langchain.agents.middleware import after_agent, AgentState
from langgraph.runtime import Runtime
from typing import Any

@after_agent(can_jump_to=["end"])
def my_hook(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    ...
```

## Example: Safety Guardrail

```python
from typing import Any
from langchain.agents.middleware import after_agent, AgentState
from langgraph.runtime import Runtime
from langchain.messages import AIMessage

# Initialize safety model (use a fast, lightweight model in production)
safety_model = None  # Would be initialized: init_chat_model("gpt-4o-mini")

@after_agent(can_jump_to=["end"])
def safety_guardrail(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Final safety check on complete agent response."""

    if not state.get("messages"):
        return None

    last_message = state["messages"][-1]

    if not isinstance(last_message, AIMessage):
        return None

    # Check for potentially harmful patterns in complete response
    harmful_patterns = [
        "self-harm", "suicide", "kill", "hurt yourself",
        "illegal activity", "how to make bombs"
    ]

    content_lower = last_message.content.lower()

    for pattern in harmful_patterns:
        if pattern in content_lower:
            # Replace with safe response
            if hasattr(state["messages"][-1], "content"):
                state["messages"][-1].content = "I can't help with that. Please seek appropriate resources."
            return {"response_sanitized": True}

    return None
```

## Example: Session Summary Generator

```python
from typing import Any
from datetime import datetime
from langchain.agents.middleware import after_agent, AgentState
from langgraph.runtime import Runtime

# In production, use a proper storage backend
_session_summaries: dict[str, dict] = {}

@after_agent
def generate_session_summary(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Generate and store conversation summary after agent completes."""

    conversation_id = state.get("conversation_id", "default")

    if not state.get("messages"):
        return None

    # Collect conversation metadata
    message_count = len(state["messages"])
    first_msg = state["messages"][0] if state["messages"] else None
    last_msg = state["messages"][-1] if state["messages"] else None

    summary = {
        "conversation_id": conversation_id,
        "completed_at": datetime.now().isoformat(),
        "message_count": message_count,
        "user_query": first_msg.content if hasattr(first_msg, "content") else None,
        "final_response": last_msg.content if hasattr(last_msg, "content") else None,
        "token_usage": state.get("token_usage", {}),
    }

    _session_summaries[conversation_id] = summary

    return {"session_summary": summary}
```

## Example: Analytics Logger

```python
from typing import Any
from datetime import datetime
from langchain.agents.middleware import after_agent, AgentState
from langgraph.runtime import Runtime

# Mock analytics queue (use Celery, Kafka, etc. in production)
_analytics_events: list[dict] = []

@after_agent
def log_to_analytics(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Log agent completion event to analytics pipeline."""

    event = {
        "timestamp": datetime.now().isoformat(),
        "conversation_id": state.get("conversation_id", "unknown"),
        "user_id": state.get("user_id", "anonymous"),
        "agent_name": state.get("agent_name", "default"),
        "message_count": len(state.get("messages", [])),
        "token_usage": state.get("token_usage", {}),
        "success": not state.get("error"),
        "duration_ms": runtime.extra.get("duration_ms", 0) if hasattr(runtime, "extra") else None
    }

    _analytics_events.append(event)

    return {"analytics_logged": True}
```

## Example: Response Formatter

```python
from typing import Any
from langchain.agents.middleware import after_agent, AgentState
from langgraph.runtime import Runtime
import re

@after_agent
def format_final_response(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Clean up and format the final response."""

    if not state.get("messages"):
        return None

    last_message = state["messages"][-1]

    if not hasattr(last_message, "content"):
        return None

    content = last_message.content

    # Clean up excessive whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()

    # Fix common LLM formatting issues
    content = content.replace("* ", "• ")
    content = content.replace("**", "")

    # Update the final message
    if hasattr(state["messages"][-1], "content"):
        state["messages"][-1].content = content

    return {"response_formatted": True}
```

## Execution Position

```
Agent Execution Flow:
┌─────────────────────────────────────────────────────────┐
│  @before_agent  ──►  [Agent Loop]  ──►  @after_agent   │
│       │                    │                    │       │
│   Entry gate          Model calls           Exit gate   │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
                   Returns to user
```

## Notes

- Runs **once per agent invocation** - after the agent loop completes
- Use `can_jump_to` if you need to route to additional processing nodes
- Final state is frozen when this hook runs
- Ideal for external system integration (logging, storage)
- Multiple `@after_agent` hooks run in **reverse order** (last to first)
- State updates here affect what gets returned to the caller