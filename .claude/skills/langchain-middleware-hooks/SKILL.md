---
name: langchain-middleware-hooks
description: Use when working with LangChain v1 middleware hooks or callbacks. Covers @before_agent, @before_model, @after_model, @after_agent, @wrap_model_call, and @wrap_tool_call. This skill serves as an index pointing to detailed documentation for each specific hook.
---

# LangChain Middleware Hooks Overview

LangChain v1 provides **6 middleware hooks** for intercepting and controlling agent execution at different points. Each hook serves a specific purpose and runs at a specific time in the execution lifecycle.

## Hooks Quick Reference

| Hook | When It Fires | Use Case |
|------|--------------|----------|
| `@before_agent` | Once before agent starts | Authentication, rate limiting, input validation |
| `@before_model` | Before each model call | Dynamic prompt injection, intent detection |
| `@after_model` | After each model response | Response logging, token tracking, output filtering |
| `@after_agent` | Once after agent completes | Final safety check, session summary, analytics |
| `@wrap_model_call` | Around each model call | Retry logic, caching, cost tracking |
| `@wrap_tool_call` | Around each tool call | Tool logging, access control, caching |

## Execution Flow

```
┌────────────────────────────────────────────────────────────────┐
│  @before_agent  ──►  [Agent Loop]                              │
│       │                  │                                     │
│       │            ┌────┴────┐                                 │
│       │            │         │                                 │
│       │     @before_model  @after_model                        │
│       │            │         │                                 │
│       │     ┌──────┴───┐     │                                 │
│       │     │ wrap_    │     │                                 │
│       │     │ model_   │     │                                 │
│       │     │ call     │     │                                 │
│       │     └──────┬───┘     │                                 │
│       │            │         │                                 │
│       │     @wrap_tool_call  │  (when tools are called)        │
│       │            │         │                                 │
│       │            └────┬────┘                                 │
│       │                 │                                      │
│       └──────►  @after_agent                                   │
└────────────────────────────────────────────────────────────────┘
```

## Hook Details

### 1. `@before_agent` - Entry Gate
- **Fires**: Once per agent invocation, before any processing
- **Best for**: Authentication, rate limiting, content filtering, request validation
- **Can short-circuit**: Yes (`jump_to: "end"`)

**Example use cases:**
- Block requests with banned keywords
- Enforce rate limits per user
- Validate authentication tokens

### 2. `@before_model` - Pre-LLM Processing
- **Fires**: Before each model call inside the agent loop
- **Best for**: Dynamic prompt injection, context enrichment, message transformation
- **Can short-circuit**: Yes (`jump_to` to different nodes)

**Example use cases:**
- Inject intent-specific system prompts
- Truncate messages approaching token limits
- Add relevant tool descriptions based on user query

### 3. `@after_model` - Post-LLM Processing
- **Fires**: After each model response inside the agent loop
- **Best for**: Response logging, content moderation, token counting
- **Can short-circuit**: No (state updates only)

**Example use cases:**
- Log all LLM responses for debugging
- Track token usage per call
- Sanitize sensitive data from responses

### 4. `@after_agent` - Exit Gate
- **Fires**: Once after agent loop completes
- **Best for**: Final safety checks, session summary, external logging
- **Can short-circuit**: Yes (via `can_jump_to`)

**Example use cases:**
- Run safety guardrail on complete response
- Generate conversation summary
- Log to analytics pipeline

### 5. `@wrap_model_call` - Around LLM
- **Fires**: Around each model call (outermost wraps innermost)
- **Best for**: Retry logic, caching, request/response transformation
- **Full control**: Call handler zero, one, or multiple times

**Example use cases:**
- Retry with exponential backoff on failure
- Cache responses for identical requests
- Track cost per model invocation

### 6. `@wrap_tool_call` - Around Tools
- **Fires**: Around each tool call (outermost wraps innermost)
- **Best for**: Tool call logging, access control, caching
- **Full control**: Call handler zero, one, or multiple times

**Example use cases:**
- Log all tool calls and results
- Restrict tool access based on permissions
- Cache tool results for idempotent calls

## Detailed Documentation

For complete technical details, function signatures, and best-practice code examples for each hook, refer to the individual skill files:

- **@before_agent** → `before_agent.md`
- **@before_model** → `before_model.md`
- **@after_model** → `after_model.md`
- **@after_agent** → `after_agent.md`
- **@wrap_model_call** → `wrap_model_call.md`
- **@wrap_tool_call** → `wrap_tool_call.md`

## Return Values Summary

| Hook | Return Type | Short-circuit Support |
|------|-------------|----------------------|
| `@before_agent` | `dict[str, Any] \| None` | Yes (`jump_to`) |
| `@before_model` | `dict[str, Any] \| None` | Yes (`jump_to`) |
| `@after_model` | `dict[str, Any] \| None` | No |
| `@after_agent` | `dict[str, Any] \| None` | Yes (`can_jump_to`) |
| `@wrap_model_call` | `ModelResponse \| ExtendedModelResponse` | N/A (you call handler) |
| `@wrap_tool_call` | `ToolResponse` | N/A (you call handler) |

## Choosing the Right Hook

**Question to ask yourself:**

1. **When do you need to act?**
   - Before any processing starts → `@before_agent`
   - Right before the LLM sees input → `@before_model`
   - Right after the LLM responds → `@after_model`
   - After everything is done → `@after_agent`

2. **Do you need retry/caching logic?**
   - Around model calls → `@wrap_model_call`
   - Around tool calls → `@wrap_tool_call`

3. **Do you need to modify state or short-circuit?**
   - Modify state only → `@after_model`
   - Short-circuit/redirect → `@before_agent`, `@before_model`, `@after_agent`