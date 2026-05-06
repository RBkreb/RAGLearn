# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A RAG (Retrieval Augmented Generation) Q&A bot built with LangChain and Ollama. The system indexes ITU standards documents and answers user questions by retrieving relevant content and generating responses.

**Source data**: ITU T-REC-X.200 document in `./input/`
**LLM**: Qwen3.5:0.8b (chat), Qwen3-embedding:4b (embeddings)

## Common Commands

```bash
# Run all unit tests
E:/Uagent/venv/Scripts/python.exe -m pytest test/unit/ -v

# Run with coverage report
E:/Uagent/venv/Scripts/python.exe -m pytest test/unit/ --cov=E:/Uagent/src --cov-report=term-missing

# Run a single test file
E:/Uagent/venv/Scripts/python.exe -m pytest test/unit/test_xxx.py -v

# Run a specific test
E:/Uagent/venv/Scripts/python.exe -m pytest test/unit/test_xxx.py::test_name -v
```

**Always use the venv Python** (`E:/Uagent/venv/Scripts/python.exe`), never the system Python.

## Architecture (Intended)

```
src/
├── config.py           # Configuration management
├── models/
│   ├── llm.py         # Ollama LLM wrapper (Qwen3.5:0.8b)
│   └── embedding.py   # Ollama embedding model (Qwen3-embedding:4b)
├── indexing/
│   ├── parser.py      # Document parsing (PDF, images)
│   ├── chunker.py     # Text chunking
│   └── vector_index.py # ChromaDB vector indexing
├── retrieval/
│   └── hybrid_retriever.py  # Vector + graph retrieval
├── agents/
│   └── rag_agent.py   # LangChain RAG agent
├── graph/
│   └── (graph rag components)
└── pipeline.py        # Main RAG pipeline orchestration
```

**Data flow**: Input docs → Parser → Chunker → Vector index (ChromaDB) + Knowledge Graph → Hybrid Retriever → RAG Agent → LLM → Answer

## Key Technologies

- **LangChain** - Agent framework
- **LlamaIndex** - RAG indexing
- **ChromaDB** - Vector store
- **Ollama** - Local LLM serving (Qwen models)

## Testing Requirements

- Follow TDD: write tests before implementation
- 80% line coverage minimum (90% for critical modules)
- Tests in `test/unit/` with `test_*.py` naming
- Mock external dependencies (network, filesystem) in unit tests
- Use `test-specialist` subagent for test tasks

## Code Rules

Project-specific rules are in `.claude/rules/`:
- `code-style.md` - Python style (max 500 lines/file, 50 lines/function, type annotations required)
- `testing.md` - Testing standards (TDD, coverage thresholds, mock principles)

## MCP Servers

Configured MCP servers for documentation:
- `langchain` - LangChain docs
- `llama-index-docs` - LlamaIndex docs
