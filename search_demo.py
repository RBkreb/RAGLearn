"""Minimal retrieval demo: embed news and query via InMemoryStore."""

import sys
import logging
import os
from pathlib import Path
from typing import Any

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

os.environ.update({
    "LLAMA_VERBOSE": "0",
    "HF_HUB_VERBOSITY": "error",
    "VLLM_LOGGING_LEVEL": "ERROR",
    "TRANSFORMERS_VERBOSITY": "error",
    "GGML_OPRINT": "0",
})
logging.basicConfig(level=logging.ERROR)
for name in ["transformers", "huggingface_hub", "llama", "vllm", "accelerate", "ggml"]:
    logging.getLogger(name).setLevel(logging.ERROR)

from src.config import PipelineConfig
from src.pipeline.embedding_service import EmbeddingService
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_by_line(texts: list[str], chunk_size: int = 500) -> list[dict[str, Any]]:
    """Split texts by line, each line becomes a chunk.

    Args:
        texts: List of text strings (each string is one news item).
        chunk_size: Maximum characters per chunk; if line exceeds this,
            apply recursive character splitting without overlap.

    Returns:
        List of chunk dictionaries with 'content' and 'metadata' keys.
    """
    all_chunks: list[dict[str, Any]] = []

    for text in texts:
        # If line fits within chunk_size, keep as single chunk
        if len(text) <= chunk_size:
            all_chunks.append({"content": text, "metadata": {"source": ""}})
        else:
            # Split long lines without overlap
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=0,  # No overlap for line-based chunks
            )
            for doc in splitter.create_documents([text]):
                all_chunks.append({"content": doc.page_content, "metadata": {"source": ""}})

    return all_chunks


def parse_news(doc_path: Path, max_items: int = 20) -> list[str]:
    """Parse news items from documents.txt.

    Each line is a separate news item with format: [timestamp] ，正文：content
    Extract only the content after "正文：".
    """
    texts: list[str] = []
    with open(doc_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Extract content after "正文："
            if "正文：" in line:
                content = line.split("正文：", 1)[1]
                texts.append(content)
                if len(texts) >= max_items:
                    break
    return texts


def main() -> None:
    """Run minimal retrieval demo."""
    config = PipelineConfig()
    doc_path = config.input_dir / "documents.txt"

    # 1. Parse news (each line is one news item)
    news_texts = parse_news(doc_path, max_items=20)
    print(f"Loaded {len(news_texts)} news items")

    # 2. Chunk by line (no overlap, smaller chunk size)
    chunks = chunk_by_line(texts=news_texts, chunk_size=250)
    print(f"Created {len(chunks)} chunks")

    # 3. Create EmbeddingService and embed chunks
    embed_service = EmbeddingService(
        model_path="model/Qwen3-Embedding-4B-GGUF/Qwen3-Embedding-4B-Q4_K_M.gguf",
        n_ctx=config.embedding_n_ctx,
        n_threads=config.embedding_n_threads,
        n_batch=config.embedding_n_batch,
    )
    embeddings = embed_service.get_embeddings()

    # 4. Build InMemoryVectorStore with embedded documents
    docs = [
        Document(page_content=c["content"], metadata=c["metadata"])
        for c in chunks
    ]
    vector_store = InMemoryVectorStore(embedding=embeddings)
    vector_store.add_documents(docs)
    print(f"InMemoryVectorStore ready with {len(docs)} documents")

    # 5. Query retrieval (keywords only, no natural language)
    queries = [
        "非洲 俄乌 调解",
        "法院 游戏外挂 米哈游",
        "工业材料 研发 纳米",
    ]

    print("\n--- Retrieval Results ---\n")
    for query in queries:
        print(f"Query: {query}")
        results = vector_store.similarity_search_by_vector(
            embeddings.embed_query(query), k=2
        )
        for i, doc in enumerate(results, 1):
            print(f"  [{i}] {doc.page_content}")
        print()


if __name__ == "__main__":
    main()