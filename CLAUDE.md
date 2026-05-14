# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Q&A bot built with LangChain and OpenAI-compatible interface. Supports prefix routing and conversation memory for answering user questions via local LLMs.

## Prerequisites

- Local LLM service running at `http://127.0.0.1:1234` (OpenAI-compatible)
- Chat model using `langchain_openai.ChatOpenAI`
- llama-cpp-python with GGUF embedding model

## Common Commands

**Always use venv Python**: `./venv/Scripts/python.exe`

## Testing Requirements

- Follow **TDD**: write tests before implementation
- **80% line coverage** minimum (90% for critical modules: retrieval, agents, pipeline)
- Tests in `test/unit/` with `test_*.py` naming
- **Mock external dependencies** (network calls to Ollama, filesystem, ChromaDB) in unit tests
- Integration tests should use real ChromaDB with isolated test database
- **Test Flow**: Write implementation code and test code → hand over to `test-specialist` to execute tests and verify coverage

## Code Rules

Project rules in `.claude/rules/`:
- `code-style.md` - Python style: max 500 lines/file, 50 lines/function, 300 lines/class, type annotations required, specific exception handling
- `testing.md` - Testing standards: TDD workflow, coverage thresholds, mock principles, fixture guidelines
- `base.md` - General development rules (stop on failures after 3 attempts, use venv always, delegate missing packages to human)

## Subagents

- `test-specialist` - Execute and review pre-written test code (test code is written by main agent before handing over to test-specialist)

## MCP Servers

Configured for documentation lookup:
- `langchain` - LangChain framework docs

## Prerequisites

- Local LLM service running at `http://127.0.0.1:1234` (OpenAI-compatible)
- Chat model using `langchain_openai.ChatOpenAI`
