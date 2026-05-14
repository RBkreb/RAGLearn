---
name: langchain-wrap-tool-call-hook
description: Use when implementing @wrap_tool_call middleware hook in LangChain v1. Wraps around each tool call - ideal for tool call logging, retry logic, caching tool results, input/output transformation, or access control on tool execution.
---

# LangChain `@wrap_tool_call` Hook

## When to Use

The `@wrap_tool_call` hook wraps **around each tool call**, giving full control over tool execution. Use it for:

- **Tool Call Logging** - Log which tools are called with what arguments
- **Retry Logic** - Automatic retry with backoff on tool failures
- **Caching** - Cache tool results for identical calls
- **Input Transformation** - Transform tool arguments before execution
- **Output Transformation** - Transform or filter tool results
- **Access Control** - Restrict which tools can be called by whom
- **Rate Limiting** - Limit rate of specific tool calls

## Purpose

Provides imperative control over tool execution. You decide whether to call the handler, how many times, and can inspect/modify both input arguments and output.

## Return Value

`ToolResponse`:
- Call `handler(request)` to execute the tool normally
- Can call `handler` zero times (block), once, or multiple times (retry)
- Return the final `ToolResponse`

## Signature

```python
from langchain.agents.middleware import wrap_tool_call, ToolRequest, ToolResponse
from typing import Callable

@wrap_tool_call
def my_wrapper(
    request: ToolRequest,
    handler: Callable[[ToolRequest], ToolResponse],
) -> ToolResponse:
    ...
```

## Example: Tool Call Logger

```python
from typing import Any
from datetime import datetime
from langchain.agents.middleware import wrap_tool_call, ToolRequest, ToolResponse
from typing import Callable

@wrap_tool_call
def log_tool_calls(
    request: ToolRequest,
    handler: Callable[[ToolRequest], ToolResponse],
) -> ToolResponse:
    """Log all tool calls with arguments and results."""

    print(f"[{datetime.now().isoformat()}] Tool call: {request.tool_name}")
    print(f"  Arguments: {request.tool_args}")

    result = handler(request)

    print(f"[{datetime.now().isoformat()}] Tool result: {request.tool_name}")
    print(f"  Response: {str(result)[:200]}...")

    return result
```

## Example: Retry with Backoff

```python
from typing import Any
import time
from langchain.agents.middleware import wrap_tool_call, ToolRequest, ToolResponse
from typing import Callable

@wrap_tool_call
def retry_tool_calls(
    request: ToolRequest,
    handler: Callable[[ToolRequest], ToolResponse],
) -> ToolResponse:
    """Retry failed tool calls with exponential backoff."""

    max_retries = 3
    base_delay = 0.5
    retries_allowed = {"search", "api_call", "database_query"}  # Only retry safe idempotent tools

    # Don't retry dangerous tools
    if request.tool_name not in retries_allowed:
        return handler(request)

    for attempt in range(max_retries):
        try:
            return handler(request)
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            delay = base_delay * (2 ** attempt)
            print(f"Tool {request.tool_name} attempt {attempt + 1} failed: {e}")
            print(f"Retrying in {delay}s...")
            time.sleep(delay)

    return handler(request)
```

## Example: Result Cacher

```python
from typing import Any
import hashlib
import json
from langchain.agents.middleware import wrap_tool_call, ToolRequest, ToolResponse
from typing import Callable

# In-memory cache (use Redis in production)
_tool_cache: dict[str, ToolResponse] = {}
ENABLE_CACHE = True

def _cache_key(tool_name: str, tool_args: dict) -> str:
    """Generate cache key from tool name and arguments."""
    return hashlib.sha256(
        json.dumps({"tool": tool_name, "args": tool_args}, sort_keys=True).encode()
    ).hexdigest()

@wrap_tool_call
def cache_tool_results(
    request: ToolRequest,
    handler: Callable[[ToolRequest], ToolResponse],
) -> ToolResponse:
    """Cache tool results for identical calls."""

    if not ENABLE_CACHE:
        return handler(request)

    cache_key = _cache_key(request.tool_name, request.tool_args)

    if cache_key in _tool_cache:
        print(f"Cache hit for {request.tool_name}")
        return _tool_cache[cache_key]

    result = handler(request)
    _tool_cache[cache_key] = result

    return result
```

## Example: Input Sanitizer

```python
from typing import Any
import re
from langchain.agents.middleware import wrap_tool_call, ToolRequest, ToolResponse
from typing import Callable

SENSITIVE_PATTERNS = [
    (r'\b\d{3}-\d{2}-\d{4}\b', 'XXX-XX-XXXX'),  # SSN
    (r'\b\d{16}\b', 'XXXX-XXXX-XXXX-XXXX'),      # Credit card
    (r'password["\s:=]+\S+', 'password=***'),    # Passwords
]

@wrap_tool_call
def sanitize_tool_inputs(
    request: ToolRequest,
    handler: Callable[[ToolRequest], ToolResponse],
) -> ToolResponse:
    """Sanitize sensitive data from tool arguments before execution."""

    sanitized_args = dict(request.tool_args)

    for pattern, replacement in SENSITIVE_PATTERNS:
        for key, value in sanitized_args.items():
            if isinstance(value, str):
                sanitized_args[key] = re.sub(pattern, replacement, value)

    # Create new request with sanitized args
    sanitized_request = ToolRequest(
        tool_name=request.tool_name,
        tool_args=sanitized_args,
        extra=request.extra
    )

    print(f"Executing {request.tool_name} with sanitized args")
    return handler(sanitized_request)
```

## Example: Access Control

```python
from typing import Any
from langchain.agents.middleware import wrap_tool_call, ToolRequest, ToolResponse
from typing import Callable

# Define which tools require which permissions
TOOL_PERMISSIONS = {
    "delete_database": ["admin"],
    "write_file": ["editor", "admin"],
    "send_email": ["user", "admin"],
    "read_file": ["user", "editor", "admin"],
    "execute_code": ["developer", "admin"],
}

# Track current user permissions (would come from auth system)
_user_permissions: dict[str, list[str]] = {}

def set_user_permissions(user_id: str, permissions: list[str]):
    _user_permissions[user_id] = permissions

@wrap_tool_call
def access_control(
    request: ToolRequest,
    handler: Callable[[ToolRequest], ToolResponse],
) -> ToolResponse:
    """Restrict tool access based on user permissions."""

    user_id = request.extra.get("user_id", "anonymous") if hasattr(request, "extra") else "anonymous"
    user_perms = _user_permissions.get(user_id, [])

    required_perms = TOOL_PERMISSIONS.get(request.tool_name, [])

    # If no permissions required, allow
    if not required_perms:
        return handler(request)

    # Check if user has any required permission
    if not any(perm in user_perms for perm in required_perms):
        return ToolResponse(
            tool_name=request.tool_name,
            error=f"Access denied: {request.tool_name} requires {required_perms}"
        )

    return handler(request)
```

## Example: Rate Limiter

```python
from typing import Any
import time
from collections import defaultdict
from langchain.agents.middleware import wrap_tool_call, ToolRequest, ToolResponse
from typing import Callable

# Rate limiting state
_call_times: defaultdict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 10  # calls per window
RATE_WINDOW = 60.0  # seconds

@wrap_tool_call
def rate_limit_tools(
    request: ToolRequest,
    handler: Callable[[ToolRequest], ToolResponse],
) -> ToolResponse:
    """Rate limit tool calls per tool type."""

    tool_name = request.tool_name
    now = time.time()

    # Clean old calls outside window
    _call_times[tool_name] = [
        t for t in _call_times[tool_name]
        if now - t < RATE_WINDOW
    ]

    # Check rate limit
    if len(_call_times[tool_name]) >= RATE_LIMIT:
        return ToolResponse(
            tool_name=tool_name,
            error=f"Rate limit exceeded for {tool_name}. Try again later."
        )

    # Record this call
    _call_times[tool_name].append(now)

    return handler(request)
```

## Execution Position

```
wrap_tool_call nests around tool execution:
┌─────────────────────────────────────────────────────────┐
│  Middleware1                                              │
│    ┌─────────────────────────────────────────────────┐   │
│    │  Middleware2                                   │   │
│    │    ┌─────────────────────────────────────────┐ │   │
│    │    │  Tool Call (handler(request))          │ │   │
│    │    └─────────────────────────────────────────┘ │   │
│    └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Notes

- **Nested execution**: First middleware wraps all others (outermost = first declared)
- Full control: call handler zero, one, or multiple times
- Can inspect and modify both request (tool args) and response
- `ToolRequest.tool_args` contains the arguments passed to the tool
- `ToolResponse` contains the result or error from tool execution
- Ideal for cross-cutting concerns (logging, caching, retries, access control)
- Works at the individual tool call level, not the agent level