# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A RAG (Retrieval Augmented Generation) Q&A bot for indexing ITU T-REC-X.200 standards documents and answering user questions via local GGUF LLMs.

**Models**: Qwen3.5-4B-Q6_K.gguf (chat) and Qwen3-Embedding-0.6B-Q8_0.gguf (embeddings) loaded via llama-cpp-python
**Vector Store**: ChromaDB (persisted at `./chroma_db`)
**Framework**: LangChain (ChatLlamaCpp, LlamaCpp embedding wrapper)

## Common Commands

**Always use venv Python**: `E:/Uagent/venv/Scripts/python.exe`

```bash
# Run full demo (index + query)
E:/Uagent/venv/Scripts/python.exe main.py

# Query-only mode (load persisted index)
E:/Uagent/venv/Scripts/python.exe main.py --query

# Run all unit tests
E:/Uagent/venv/Scripts/python.exe -m pytest test/unit/ -v

# Run with coverage report
E:/Uagent/venv/Scripts/python.exe -m pytest test/unit/ --cov=src --cov-report=term-missing

# Run a single test file
E:/Uagent/venv/Scripts/python.exe -m pytest test/unit/test_config.py -v

# Run a specific test
E:/Uagent/venv/Scripts/python.exe -m pytest test/unit/test_pipeline.py::test_name -v
```

## Architecture

```
src/
├── config.py              # Dataclasses: RAGConfig, LlamaCppConfig, IndexConfig
├── pipeline.py            # RAGPipeline orchestration (build_pipeline, load_pipeline)
├── exceptions.py          # Custom exceptions: RAGError, PipelineError, RetrievalError, etc.
├── models/
│   ├── llm.py            # LlamaCppLLMWrapper (ChatLlamaCpp)
│   └── embedding.py      # LlamaCppEmbeddingWrapper (llama_cpp.Llama with embedding=True)
├── indexing/
│   ├── parser.py         # DocumentParser (markdown)
│   ├── chunker.py        # TextChunker (configurable chunk_size/overlap)
│   └── vector_index.py   # ChromaIndexManager (ChromaDB wrapper)
├── retrieval/
│   └── hybrid_retriever.py # HybridRetriever (embedding + similarity search)
└── agents/
    └── rag_agent.py       # RAGAgent (retrieve → prompt → LLM → answer)
```

**Data Flow**: Input docs → Parser → Chunker → Embedding → ChromaDB → HybridRetriever → RAGAgent → ChatLlamaCpp → Answer

**Key Classes**:
- `RAGPipeline` in `pipeline.py` - Main orchestrator with `index_documents()`, `query()`, `query_with_sources()`
- `HybridRetriever` in `retrieval/hybrid_retriever.py` - Retrieves chunks via cosine similarity search
- `RAGAgent` in `agents/rag_agent.py` - Combines retrieval context into prompt, returns `AnswerResult`
- `ChromaIndexManager` in `indexing/vector_index.py` - ChromaDB CRUD with `create_index()`, `add_chunks()`, `similarity_search()`

## Configuration

Models are loaded directly via llama-cpp-python from GGUF files (not Ollama):

| Config | Default | Description |
|--------|---------|-------------|
| `llamacpp.model_path` | `./model/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q6_K.gguf` | Chat model path |
| `llamacpp.embedding_model_path` | `./model/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf` | Embedding model path |
| `index.persist_directory` | `./chroma_db` | ChromaDB storage |
| `index.chunk_size` | `500` | Text chunk size |
| `index.chunk_overlap` | `50` | Chunk overlap |

## Testing Requirements

- Follow **TDD**: write tests before implementation
- **80% line coverage** minimum (90% for critical modules: retrieval, agents, pipeline)
- Tests in `test/unit/` with `test_*.py` naming
- **Mock external dependencies** (filesystem, ChromaDB) in unit tests - do not mock the LLM/embedding wrappers themselves
- Use `test-specialist` subagent for test tasks per project rules

## Code Rules

Project rules in `.claude/rules/`:
- `code-style.md` - Python style: max 500 lines/file, 50 lines/function, 300 lines/class, type annotations required, specific exception handling
- `testing.md` - Testing standards: TDD workflow, coverage thresholds, mock principles

## MCP Servers

Configured for documentation lookup:
- `langchain-architecture` - LangChain framework patterns
- `llama-index-docs` - LlamaIndex docs
