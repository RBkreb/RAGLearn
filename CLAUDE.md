# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **RAG (Retrieval-Augmented Generation) system** for Chinese document retrieval with hybrid search:
- **ChromaDB** for vector storage and semantic search
- **BM25** (with jieba Chinese tokenization) for keyword retrieval
- **HyDE** (Hypothetical Document Embeddings) to enhance query understanding
- **RRF + CrossEncoder two-stage reranking** combines BM25 and vector scores, then reranks with a transformer cross-encoder
- **Threshold-based context selection** dynamically picks single or multiple context chunks based on similarity gaps
- **DeepEval evaluation** with AnswerRelevancy, Faithfulness, ContextualPrecision, ContextualRecall, ContextualRelevancy metrics

## Architecture

```
src/
├── chain.py                # Main chain: HyDE agent → BM25/vector hybrid search → RRF rerank
│                           # → CrossEncoder rerank → threshold-based context → answer agent
├── config.py               # All configs: LlmConfig, HyDEConfig, RAGConfig, EmbedModelConfig, IndexConfig
├── pipeline/pipe.py        # Document indexing pipeline (split → embed → store → BM25 index)
├── model/
│   ├── llm.py              # LLM wrapper (ChatOpenAI-compatible, local)
│   └── embedm.py           # Embedding model wrapper (OpenAIEmbeddings-compatible)
├── chunker/
│   ├── line_splitter.py    # Line-based splitting with hash metadata
│   └── jsonl_splitter.py   # JSONL document splitting with hash metadata
└── utils/
    ├── bm25.py             # BM25 retriever with jieba tokenization (bm25s)
    └── hash.py             # SHA256 hash for document content
tests/
└── evals/
    ├── metrics.py          # Shared DeepEval metric definitions
    ├── smoke_test.py       # Quick single-QA eval smoke test
    └── test_in_code.py     # Batch evaluation runner with multiple metrics
example/
├── BM25_eg.py              # BM25 standalone usage example
└── deepeval_eg.py          # DeepEval metric usage example
test/
└── unit/
    └── test_bm25.py        # Unit tests for BM25Retriever

Top-level scripts:
├── main.py                 # QA evaluation pipeline (loads qa_pairs.jsonl, runs chain, saves results)
├── embed_demo.py           # Quick document indexing entry point
└── extract_datasets.py     # SQuAD v2.0 → JSONL dataset extractor
```

## Commands

**Run unit tests:**
```bash
cd e:\Uagent && venv\Scripts\python -m pytest test/unit/test_bm25.py -v
```

**Run eval tests:**
```bash
cd e:\Uagent && venv\Scripts\python tests/evals/smoke_test.py
cd e:\Uagent && venv\Scripts\python tests/evals/test_in_code.py
```

**Index documents:**
```bash
cd e:\Uagent && venv\Scripts\python embed_demo.py
```

**Run QA evaluation pipeline:**
```bash
cd e:\Uagent && venv\Scripts\python main.py
```

**Extract datasets from SQuAD:**
```bash
cd e:\Uagent && venv\Scripts\python extract_datasets.py
```

## Configuration

All configs in `src/config.py`:

| Class | Key Params |
|---|---|
| `LlmConfig` | model_name="qwen3.5-4b", base_url="http://127.0.0.1:1234/v1", temperature=0.8 |
| `HyDEConfig(LlmConfig)` | model_name="qwen3.5-4b", temperature=0.75, HYDE_PROMPT for hypothetical document generation |
| `RAGConfig(LlmConfig)` | model_name="lfm2-1b-rag", temperature=0.05, strict ANSWER_PROMPT |
| `EmbedModelConfig` | model_name="text-embedding-qwen3-embedding-0.6b", dimensions=1024, n_ctx=1024 |
| `IndexConfig` | chunk_size=600, chunk_overlap=60, persist_directory="./chroma_db" |

Two separate LLMs: **HyDE LLM** (qwen3.5-4b, creative) and **RAG LLM** (lfm2-1b-rag, strict).

## Key Patterns

- **Hash lookup**: Documents stored with SHA256 hash in Chroma metadata; BM25 results look up vectors via hash
- **HyDE flow**: Query → HyDE agent generates hypothetical document + keywords → hybrid search → RRF + CrossEncoder rerank → answer
- **Threshold logic**: If max similarity > threshold and gap > gap_threshold → single best chunk; if avg/mid also high → multi-chunk; retries up to 3 times with expanding search
- **CrossEncoder reranker**: Uses `Qwen/Qwen3-Reranker-0.6B` via HuggingFace, wraps LangChain's `CrossEncoderReranker` with custom `compress_documents` returning (Document, score) tuples
- **Chinese tokenization**: Uses jieba for BM25 via `bm25s` library with custom tokenizer override
- **Two chunker modes**: `plain` (line-based via `LineSplitter`) and `jsonl` (JSONL entries via `JsonlSplitter`)
- **Evaluation**: DeepEval metrics (AnswerRelevancy, Faithfulness, ContextualPrecision, ContextualRecall, ContextualRelevancy) using local GPTModel judge
