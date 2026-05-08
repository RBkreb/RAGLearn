"""Demo script for testing RAG with LLM tool calling."""

import os
import logging

os.environ.update({
    "LLAMA_VERBOSE": "0",
    "HF_HUB_VERBOSITY": "error",
    "VLLM_LOGGING_LEVEL": "ERROR",
    "TRANSFORMERS_VERBOSITY": "error"
})
 
logging.basicConfig(level=logging.ERROR)
for name in ["transformers", "huggingface_hub", "llama", "vllm", "accelerate","ggml"]:
    logging.getLogger(name).setLevel(logging.ERROR)

from pathlib import Path

from src.config import PipelineConfig
from src.pipeline import RAGPipeline
from src.llm_service import LLMService
from src.tools.rag_tool import set_retriever



def main() -> None:
    """Test RAG pipeline with LLM using rag_retrieve tool."""
    config = PipelineConfig()
    print(f"Input dir: {config.input_dir}")
    print(f"Chroma DB path: {config.chroma_db_path}")
    print(f"Collection: {config.collection_name}")

    pipeline = RAGPipeline(config)

    if not pipeline.check_db_exists():
        print("\nNo existing database found. Running ingestion...")
        chunk_count = pipeline.run_ingestion(overwrite=True)
        print(f"Ingested {chunk_count} chunks")
    else:
        print("\nUsing existing database.")

    retriever = pipeline.get_retriever()
    set_retriever(retriever)
    print("Retriever initialized and set.")

    llm = LLMService()
    print("LLM Service initialized.")
    queries = [
        "什么是OSI模型",
    ]

    print("\n--- Testing LLM with RAG Tool ---")
    for query in queries:
        print(f"\nQuery: {query}")
        result = llm.generate(query)
        print(f"Response: {result.content}")
        if result.tool_calls:
            print(f"Tool calls: {result.tool_calls}")
        print("-" * 50)


if __name__ == "__main__":
    main()
