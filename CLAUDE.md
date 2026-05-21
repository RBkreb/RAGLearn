# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **RAG (Retrieval-Augmented Generation) system** for Chinese document retrieval with hybrid search:
- **ChromaDB** for vector storage and semantic search
- **BM25** (with jieba Chinese tokenization) for keyword retrieval
- **HyDE** (Hypothetical Document Embeddings) to enhance query understanding
- **RFF reranking** combines BM25 and vector scores

## Architecture

```
src/
├── chain.py          # Main chain: HyDE agent + BM25/vector hybrid search + answer agent
├── pipeline/pipe.py  # Document indexing pipeline (split → embed → store)
├── model/
│   ├── llm.py        # LLM wrapper (ChatOpenAI-compatible, local qwen3.5-0.8b)
│   └── embedm.py     # Embedding model wrapper (text-embedding-qwen3-embedding-0.6b)
├── chunker/
│   └── line_splitter.py  # Line-based splitting with hash metadata
└── utils/
    ├── bm25.py       # BM25 retriever with jieba tokenization
    └── hash.py       # SHA256 hash for document content
```

## Commands

**Run tests:**
```bash
cd e:\Uagent && venv\Scripts\python -m pytest test/unit/test_bm25.py -v
```

**Index documents:**
```bash
cd e:\Uagent && venv\Scripts\python embed_demo.py
```

**Run main pipeline:**
```bash
cd e:\Uagent && venv\Scripts\python main.py
```

## Configuration

All configs in `src/config.py`:
- `LlmConfig`: model_name="qwen3.5-0.8b", base_url="http://127.0.0.1:1234/v1"
- `EmbedModelConfig`: model_name="text-embedding-qwen3-embedding-0.6b", dimensions=1024
- `IndexConfig`: chunk_size=600, chunk_overlap=60, persist_directory="./chroma_db"

## Key Patterns

- **Hash lookup**: Documents are stored with SHA256 hash in Chroma metadata; BM25 results look up vectors via hash
- **HyDE flow**: Query → HyDE agent generates hypothetical document + keywords → hybrid search → reranked results → answer agent
- **Chinese tokenization**: Uses jieba for BM25, not standard whitespace tokenization

## Rules (from .claude/rules/)

- **ALWAYS use venv virtual environment** — `venv\Scripts\python`
- **Tests must use subagent** — keep main agent context clean
- **Max file length**: 500 lines, **max function length**: 50 lines
- **No bare `except:`** — catch specific exceptions
- **Coverage thresholds**: 80% overall, 90% for critical modules

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
