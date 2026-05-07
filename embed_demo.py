"""Demo script for testing embedding with GGUF model and storing in ChromaDB."""
import os
import logging
import sys

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


def main() -> None:
    """Ingest documents from input/ directory into ChromaDB via embedding pipeline."""
    config = PipelineConfig()
    print(f"Model path: {config.embedding_model_path}")
    print(f"Input dir: {config.input_dir}")
    print(f"Chroma DB: {config.chroma_db_path}")

    pipeline = RAGPipeline(config)

    overwrite = True
    if pipeline.check_db_exists():
        if "--force" in sys.argv:
            overwrite = True
        elif "--skip" in sys.argv:
            overwrite = False
        else:
            try:
                response = input("Database exists. Overwrite? (y/n): ")
                overwrite = response.lower() == "y"
            except EOFError:
                print("Non-interactive mode, skipping overwrite.")
                overwrite = False

    if overwrite:
        chunk_count = pipeline.run_ingestion(overwrite=overwrite)
        print(f"\nIngested {chunk_count} chunks into ChromaDB.")
        print(f"Database saved at: {config.chroma_db_path}")
    else:
        print("Skipped ingestion.")


if __name__ == "__main__":
    main()
