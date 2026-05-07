---
name: langchain-tool
description: |
  Design and implement LangChain tools for Python projects. Use this skill whenever:
  - User asks to create a tool for a LangChain agent/graph
  - User mentions adding a tool to their LangChain setup
  - User describes a functionality that could be a tool (search, API calls, data processing)
  - During coding, if a problem could be solved with a tool, proactively suggest it AND ask "Would you like me to create this as a tool?"
  - User wants to wrap an existing function as a LangChain tool
  - User needs to integrate tools with their existing agent
  - User asks about tool patterns (error handling, state access, returning Command, etc.)
  This skill generates production-ready Python tool code and integrates it into the project.
version: 1.1.0
---

# LangChain Tool Designer

This skill helps you design, implement, and integrate LangChain tools into your Python project. Tools extend agents' capabilities — allowing them to fetch data, execute actions, and interact with external systems.

## Workflow

When triggered, follow this process:

1. **Understand the requirement** — what should the tool do, what inputs/outputs?
2. **Design the tool** — choose the simplest appropriate pattern
3. **Write the tool** — to `src/tools/<tool_name>.py`
4. **Export from `src/tools/__init__.py`**
5. **Integrate** — show how to use the tool with the existing agent/graph

**Most importantly**: when proactively suggesting a tool, END by asking "Would you like me to create this tool?" to get user confirmation before writing code.

---

## Pattern Selection Guide

Use the **simplest pattern that fits**. Don't over-engineer.

| Scenario | Pattern |
|----------|---------|
| Single function, simple args | `@tool` decorator |
| Custom name/description | `@tool("name", description="...")` |
| Structured/validated inputs | `@tool(args_schema=PydanticModel)` |
| Need runtime context (state/store) | Add `runtime: ToolRuntime` param |
| Update agent state | Return `Command` from tool |
| Wrapping existing service | Delegate to service class, don't re-instantiate |

---

## Tool Design Patterns

### 1. Simple Tool (Default Choice)

For most tools, use the `@tool` decorator — it's the simplest and most idiomatic:

```python
from langchain.tools import tool

@tool
def search_documents(query: str, top_k: int = 5) -> str:
    """Search documents for relevant content.

    Args:
        query: Search query string.
        top_k: Maximum number of results to return.

    Returns:
        Formatted search results with content snippets.
    """
    # Implementation here
    return f"Found {top_k} results for: {query}"
```

The function's docstring becomes the tool description. The function name becomes the tool name.

### 2. Custom Name and Description

Customize the tool's name and/or description using `@tool("name", description="...")`:

```python
@tool("web_search", description="Search the web for current information. Use this when answering questions about recent events or facts that may change over time.")
def search(query: str) -> str:
    """Search the web."""
    return f"Results for: {query}"
```

**When to use custom name**: When the function name is unclear, too long, or contains special characters.

**When to use custom description**: Always — the default docstring-based description is often too generic. Write a specific description that tells the LLM **when** to use this tool and **what** it returns.

**Description best practices**:
- Start with what the tool does
- Specify when to use it ("Use this when...")
- Mention input format if non-obvious

### 3. Complex Input with Pydantic

For tools needing validation or structured inputs:

```python
from pydantic import BaseModel, Field
from typing import Literal
from langchain.tools import tool

class SearchInput(BaseModel):
    """Input schema for document search."""
    query: str = Field(description="Search query string")
    filters: dict[str, str] = Field(default_factory=dict, description="Metadata filters")
    max_results: int = Field(default=10, ge=1, le=100, description="Max results, 1-100")
    search_type: Literal["semantic", "keyword"] = Field(default="semantic", description="Search algorithm")

@tool(args_schema=SearchInput)
def search_documents(
    query: str,
    filters: dict[str, str] | None = None,
    max_results: int = 10,
    search_type: str = "semantic"
) -> str:
    """Search through indexed documents using semantic or keyword search."""
    # Implementation
    return "..."
```

### 4. Accessing Runtime Context

For tools that need to read/write conversation state or store:

```python
from langchain.tools import tool, ToolRuntime

@tool
def get_conversation_summary(runtime: ToolRuntime) -> str:
    """Get a summary of the current conversation."""
    messages = runtime.state.get("messages", [])
    return f"Conversation has {len(messages)} messages"
```

### 5. Updating Agent State with Command

```python
from langchain.messages import ToolMessage
from langchain.tools import tool, ToolRuntime
from langgraph.types import Command

@tool
def set_user_name(name: str, runtime: ToolRuntime) -> Command:
    """Set the user's display name in conversation state."""
    return Command(
        update={
            "user_name": name,
            "messages": [
                ToolMessage(
                    content=f"User name set to {name}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
```

---

## File Organization

### Writing Tools

1. **Create the tool file**: `src/tools/<tool_name>.py`
2. **Update `src/tools/__init__.py`**: add export

Example `src/tools/__init__.py`:
```python
from src.tools.search_documents import search_documents

__all__ = ["search_documents"]
```

### Wrapping Existing Functions

**Do NOT modify the original function**. Instead, create a new tool that delegates to it:

```python
# src/tools/llm_tools.py
from langchain.tools import tool
from src.llm_service import LLMService

_llm_service: LLMService | None = None

def _get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

@tool
def generate_with_context(query: str, context: str) -> str:
    """Generate LLM response with conversation context."""
    service = _get_llm_service()
    return service.generate_with_context(query=query, context=context)
```

This approach:
- **Reuses** existing service (lazy loading, single instance)
- **Does not modify** the original class
- Works with `@tool` decorator (simple and clean)

---

## Integration with Existing Code

After creating a tool, show how to integrate:

```python
from src.tools import search_documents
from langgraph.prebuilt import ToolNode

# Create tool node
tool_node = ToolNode([search_documents])

# Or bind to agent
from langchain.agents import create_agent
agent = create_agent(model, tools=[search_documents])
```

---

## Proactive Suggestion

When during coding you notice a task could be a tool, **suggest it and ask for confirmation**:

```
I notice the data cleaning logic could be extracted as a LangChain tool. Benefits:
- Reusable across different agents/flows
- Easier to test in isolation
- LLM can see and invoke it explicitly

Would you like me to create this as a tool?
```

**Important**: Always ask for confirmation before writing files. Don't assume — the user may have different preferences.

---

## Return Values

| Return Type | Use When |
|------------|----------|
| `str` | Human-readable result for model to read |
| `dict` / object | Structured data model should parse fields from |
| `Command` | Updating agent state (include `ToolMessage`) |

---

## Error Handling

```python
from langgraph.prebuilt import ToolNode

# Let ToolNode handle errors gracefully (returns error to LLM as string)
tool_node = ToolNode(tools, handle_tool_errors=True)

# Custom error message
tool_node = ToolNode(tools, handle_tool_errors="Something went wrong, please try again.")
```

---

## Tool Naming Conventions

- Use `snake_case` for tool names (e.g., `search_documents`, not `searchDocuments`)
- Name should describe what the tool does: `<verb>_<noun>`
- Examples: `search_documents`, `get_weather`, `fetch_user_data`

---

## Proactive Suggestion Triggers

During coding, proactively suggest tools when the user:
- Describes a task that fetches external data (search, API calls, database queries)
- Needs to perform an action that could be parameterized
- Mentions "add a function that the agent can call"
- Describes multi-step workflows that agents excel at

**Always end suggestions with**: "Would you like me to create this as a tool?"