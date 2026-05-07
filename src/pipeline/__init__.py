"""Standalone RAG pipeline for document embedding and retrieval."""

from src.pipeline.run_pipeline import RAGPipeline
from src.pipeline.document_loader import load_documents

__all__ = ["RAGPipeline", "load_documents"]
