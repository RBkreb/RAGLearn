# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A RAG (Retrieval Augmented Generation) Q&A bot built with LangChain and Ollama. The system indexes ITU T-REC-X.200 standards documents and answers user questions by retrieving relevant content and generating responses via local LLMs.

**LLM Models**: Qwen3.5:0.8b (chat), Qwen3-embedding:4b (embeddings) served via Ollama at `http://localhost:11434`
**Vector Store**: ChromaDB (persisted at `./chroma_db`)

## Common Commands

**Always use venv Python**: `E:/Uagent/venv/Scripts/python.exe`

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

## Architecture

```
src/
├── config.py              # Configuration dataclasses (RAGConfig, OllamaConfig, IndexConfig)
├── pipeline.py            # RAGPipeline orchestration (build_pipeline, load_pipeline)
├── exceptions.py          # Custom exceptions (PipelineError, RetrievalError, etc.)
├── models/
│   ├── llm.py             # OllamaLLMWrapper for chat generation
│   └── embedding.py       # OllamaEmbeddingWrapper for vector embeddings
├── indexing/
│   ├── parser.py          # DocumentParser (PDF, images via pypdf + OCR)
│   ├── chunker.py         # TextChunker (configurable chunk_size/overlap)
│   └── vector_index.py    # ChromaIndexManager (ChromaDB wrapper)
├── retrieval/
│   └── hybrid_retriever.py # HybridRetriever combining embedding + vector search
└── agents/
    └── rag_agent.py       # RAGAgent (retrieval → prompt → LLM → answer)
```

**Data Flow**: Input docs → Parser → Chunker → Embedding → ChromaDB → HybridRetriever → RAGAgent → OllamaLLM → Answer

**Key Classes**:
- `RAGPipeline` in `pipeline.py` - Main orchestrator with `index_documents()`, `query()`, `query_with_sources()`
- `HybridRetriever` in `retrieval/hybrid_retriever.py` - Retrieves chunks via similarity search
- `RAGAgent` in `agents/rag_agent.py` - Combines retrieval context with LLM prompt

## Testing Requirements

- Follow **TDD**: write tests before implementation
- **80% line coverage** minimum (90% for critical modules: retrieval, agents, pipeline)
- Tests in `test/unit/` with `test_*.py` naming
- **Mock external dependencies** (network calls to Ollama, filesystem, ChromaDB) in unit tests
- Use `test-specialist` subagent for test tasks per project rules
- Integration tests should use real ChromaDB with isolated test database

## Code Rules

Project rules in `.claude/rules/`:
- `code-style.md` - Python style: max 500 lines/file, 50 lines/function, 300 lines/class, type annotations required, specific exception handling
- `testing.md` - Testing standards: TDD workflow, coverage thresholds, mock principles, fixture guidelines

## MCP Servers

Configured for documentation lookup:
- `langchain` - LangChain framework docs
- `llama-index-docs` - LlamaIndex docs (developers.llamaindex.ai)

## Prerequisites

- Ollama service running at `http://127.0.0.1:11434`
- Required models deployed: `qwen3.5:0.8b` and `qwen3-embedding:4b`
