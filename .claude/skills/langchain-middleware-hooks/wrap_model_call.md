---
name: langchain-wrap-model-call-hook
description: Use when implementing @wrap_model_call middleware hook in LangChain v1. Wraps around each model call - ideal for retry logic, caching, request/response logging, timeout handling, cost tracking, or transforming model inputs and outputs.
---

# LangChain `@wrap_model_call` Hook

## When to Use

The `@wrap_model_call` hook wraps **around each model call**, giving full control over execution. Use it for:

- **Retry Logic** - Automatic retry with backoff on failure
- **Caching** - Cache responses for identical requests
- **Request/Response Logging** - Log full request/response pairs
- **Timeout Handling** - Enforce timeouts on model calls
- **Cost Tracking** - Track cost per model call
- **Request Transformation** - Modify model input before calling
- **Response Transformation** - Modify model output after calling

## Purpose

Provides imperative control over the model call execution. You decide whether to call the handler, how many times, and can inspect/modify both request and response.

## Return Value

`ModelResponse` or `ExtendedModelResponse`:
- Call `handler(request)` to execute the model normally
- Can call `handler` zero times (short-circuit), once, or multiple times (retry)
- `ExtendedModelResponse` wraps response with optional `Command` for state updates

## Signature

```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def my_wrapper(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    ...
```

With state updates:
```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse, ExtendedModelResponse
from langgraph.types import Command

@wrap_model_call(state_schema=UsageTrackingState)
def track_usage(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ExtendedModelResponse:
    response = handler(request)
    return ExtendedModelResponse(
        model_response=response,
        command=Command(update={"last_model_call_tokens": 150}),
    )
```

## Example: Retry with Backoff

```python
from typing import Any
import time
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def retry_with_backoff(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Retry failed model calls with exponential backoff."""

    max_retries = 3
    base_delay = 1.0

    for attempt in range(max_retries):
        try:
            return handler(request)
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            delay = base_delay * (2 ** attempt)
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)

    # Should never reach here, but just in case
    return handler(request)
```

## Example: Response Cacher

```python
from typing import Any
import hashlib
import json
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

# Simple in-memory cache (use Redis in production)
_response_cache: dict[str, ModelResponse] = {}
ENABLE_CACHE = True

def _cache_key(request: ModelRequest) -> str:
    """Generate cache key from request messages."""
    messages_content = [
        {"type": m.type, "content": m.content}
        for m in request.messages
    ]
    return hashlib.sha256(json.dumps(messages_content, sort_keys=True).encode()).hexdigest()

@wrap_model_call
def cache_responses(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Cache model responses for identical requests."""

    if not ENABLE_CACHE:
        return handler(request)

    cache_key = _cache_key(request)

    if cache_key in _response_cache:
        print(f"Cache hit for key: {cache_key[:16]}...")
        return _response_cache[cache_key]

    response = handler(request)
    _response_cache[cache_key] = response

    return response
```

## Example: Request/Response Logger

```python
from typing import Any
import time
from datetime import datetime
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def log_model_calls(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Log all model requests and responses."""

    start_time = time.time()

    # Log request
    print(f"[{datetime.now().isoformat()}] Model request:")
    for msg in request.messages:
        print(f"  {msg.type}: {msg.content[:100]}...")

    # Execute model
    response = handler(request)

    # Log response
    duration = time.time() - start_time
    print(f"[{datetime.now().isoformat()}] Model response ({duration:.2f}s):")
    print(f"  {response.raw.get('content', 'No content')[:200]}...")

    return response
```

## Example: Cost Tracker

```python
from typing import Any
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse, ExtendedModelResponse
from langgraph.types import Command
from typing import Callable

# Pricing per 1M tokens (example rates)
TOKEN_PRICING = {
    "gpt-4o": {"input": 5.00, "output": 15.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
}

# Track total cost
_total_cost = 0.0

def estimate_tokens(text: str) -> int:
    """Rough token estimation."""
    return len(text) // 4

@wrap_model_call
def track_cost(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ExtendedModelResponse:
    """Track estimated cost of each model call."""

    global _total_cost

    # Get model name from request
    model_name = request.model_name if hasattr(request, "model_name") else "unknown"

    # Estimate input tokens
    input_text = " ".join(m.content for m in request.messages if hasattr(m, "content"))
    input_tokens = estimate_tokens(input_text)

    # Execute model
    response = handler(request)

    # Estimate output tokens
    output_content = response.raw.get("content", "") if hasattr(response, "raw") else ""
    output_tokens = estimate_tokens(output_content)

    # Calculate cost
    pricing = TOKEN_PRICING.get(model_name, {"input": 0.0, "output": 0.0})
    cost = (input_tokens / 1_000_000 * pricing["input"] +
            output_tokens / 1_000_000 * pricing["output"])

    _total_cost += cost

    return ExtendedModelResponse(
        model_response=response,
        command=Command(update={
            "last_call_cost": cost,
            "total_cost": _total_cost,
            "last_call_tokens": {"input": input_tokens, "output": output_tokens}
        })
    )
```

## Example: Timeout Enforcer

```python
from typing import Any
import signal
from functools import wraps
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Model call timed out")

@wrap_model_call
def with_timeout(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
    timeout_seconds: int = 30,
) -> ModelResponse:
    """Enforce timeout on model calls."""

    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        return handler(request)
    finally:
        # Cancel the alarm and restore previous handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
```

## Execution Position

```
wrap_model_call nests around model execution:
┌─────────────────────────────────────────────────────────┐
│  Middleware1                                              │
│    ┌─────────────────────────────────────────────────┐   │
│    │  Middleware2                                   │   │
│    │    ┌─────────────────────────────────────────┐ │   │
│    │    │  Model Call (handler(request))          │ │   │
│    │    └─────────────────────────────────────────┘ │   │
│    └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Notes

- **Nested execution**: First middleware wraps all others (outermost = first declared)
- Full control: call handler zero, one, or multiple times
- Can inspect and modify both request and response
- `ExtendedModelResponse` allows state updates via `Command`
- Ideal for cross-cutting concerns (logging, caching, retries)
- Stateless by default; use `state_schema` parameter for stateful wrapping