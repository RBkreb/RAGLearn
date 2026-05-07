---
name: RAG pipeline test patterns
description: Test patterns for RAG pipeline modules (document_loader, text_chunker, embedding_service, vector_store, rag_tool)
type: reference
---

# RAG Pipeline Test Patterns

## Source Files Tested

- `src/pipeline/document_loader.py` - `load_documents()` function
- `src/pipeline/text_chunker.py` - `chunk_documents()` function
- `src/pipeline/embedding_service.py` - `EmbeddingService` class
- `src/pipeline/vector_store.py` - `VectorStoreManager` class
- `src/tools/rag_tool.py` - `rag_retrieve` tool and `set_retriever()` function

## Key Mocking Strategies

### LlamaCppEmbeddings (embedding_service)
```python
@patch("src.pipeline.embedding_service.LlamaCppEmbeddings")
def test_get_embeddings_creates_llamacpp_instance(self, mock_llamacpp_class: MagicMock) -> None:
```
- Mock at the class level in `src.pipeline.embedding_service`
- Verify constructor args: model_path, n_ctx, n_threads

### Chroma (vector_store)
```python
@patch("src.pipeline.vector_store.Chroma")
def test_create_vector_store_calls_embedding_service(self, mock_chroma_class: MagicMock) -> None:
```
- Mock at the class level in `src.pipeline.vector_store`
- Verify both `from_texts` (create) and constructor (get)

### Filesystem (document_loader)
```python
@patch("src.pipeline.document_loader.Path.read_text")
def test_load_documents_loads_markdown_files(self, mock_read_text: MagicMock, tmp_path: Path) -> None:
```
- Mock Path.read_text for content
- Use `patch.object(Path, "iterdir", return_value=[...])` for file listing

### Global retriever state (rag_tool)
- Use `from src.tools import rag_tool` and set `rag_tool._retriever = None` in setup
- This bypasses the tool decorator's caching

## Coverage Results (per module)

| Module | Coverage |
|--------|----------|
| document_loader.py | 100% |
| text_chunker.py | 100% |
| embedding_service.py | 100% |
| vector_store.py | 100% |
| run_pipeline.py | 29% (requires integration) |

## Test Count

- test_document_loader.py: 8 tests
- test_text_chunker.py: 7 tests
- test_embedding_service.py: 13 tests
- test_vector_store.py: 20 tests
- test_rag_tool.py: 10 tests
- **Total: 56 tests**
