# Line-Then-Overlap Chunking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `chunk_documents_by_line_then_overlap` 函数，实现"先按行分割→再对每行独立重叠分块"的分块策略，并在 pipeline 中通过 `chunk_method` 配置项切换使用。

**Architecture:** 在 `text_chunker.py` 中新增 line-first 分块函数，使用 `RecursiveCharacterTextSplitter` 对每个 line chunk 独立进行重叠分块。PipelineConfig 新增 `chunk_method: Literal["overlap", "line_then_overlap"]` 配置，run_pipeline 根据配置选择分块函数。

**Tech Stack:** Python, langchain-text-splitters, pydantic, pytest

---

## File Structure

- Modify: `src/config.py` — PipelineConfig 新增 `chunk_method` 字段
- Modify: `src/pipeline/text_chunker.py` — 新增 `chunk_documents_by_line_then_overlap` 函数
- Modify: `src/pipeline/run_pipeline.py` — 根据 `chunk_method` 路由到不同分块函数
- Create: `test/unit/test_text_chunker.py` — 新增 line_then_overlap 分块测试用例

---

## Task 1: 添加 chunk_method 配置项

**Files:**
- Modify: `src/config.py:63-91` (PipelineConfig 类)

- [ ] **Step 1: 修改 PipelineConfig 新增 chunk_method 字段**

```python
class PipelineConfig(BaseModel):
    # ... existing fields ...

    chunk_method: Literal["overlap", "line_then_overlap"] = Field(
        default="overlap",
        description="Chunking method: 'overlap' uses traditional overlapping chunks, "
                    "'line_then_overlap' splits by lines first then applies overlap chunking to each line",
    )
```

- [ ] **Step 2: 验证 config 能正常导入**

Run: `E:/Uagent/venv/Scripts/python.exe -c "from src.config import PipelineConfig; print(PipelineConfig().chunk_method)"`
Expected: `overlap`

- [ ] **Step 3: 提交**

```bash
git add src/config.py
git commit -m "feat: add chunk_method config option to PipelineConfig"
```

---

## Task 2: 新增 line_then_overlap 分块函数

**Files:**
- Modify: `src/pipeline/text_chunker.py`

- [ ] **Step 1: 写测试 (TDD)**

```python
# 在 test/unit/test_text_chunker.py 中新增测试

class TestChunkDocumentsByLineThenOverlap:
    """Tests for chunk_documents_by_line_then_overlap function."""

    def test_line_then_overlap_returns_empty_for_empty_input(self) -> None:
        """Should return empty list when given empty text list."""
        from src.pipeline.text_chunker import chunk_documents_by_line_then_overlap
        result = chunk_documents_by_line_then_overlap([])
        assert result == []

    def test_line_then_overlap_splits_by_lines_first(self) -> None:
        """Should split input text by newlines into individual line chunks."""
        from src.pipeline.text_chunker import chunk_documents_by_line_then_overlap
        texts = ["line1\nline2\nline3"]
        result = chunk_documents_by_line_then_overlap(texts, line_separator="\n")
        # Should produce 3 line chunks (each line becomes a chunk)
        assert len(result) == 3

    def test_line_then_overlap_applies_overlap_to_each_line(self) -> None:
        """Should apply overlapping chunking to each line chunk independently."""
        from src.pipeline.text_chunker import chunk_documents_by_line_then_overlap
        texts = ["This is a long line that needs to be split into smaller overlapping chunks"]
        result = chunk_documents_by_line_then_overlap(
            texts,
            line_separator="\n",
            chunk_size=10,
            chunk_overlap=3,
        )
        # The single line should be further split into smaller overlap chunks
        assert all(len(chunk["content"]) <= 10 for chunk in result)

    def test_line_then_overlap_preserves_source_metadata(self) -> None:
        """Should preserve source metadata from original text."""
        from src.pipeline.text_chunker import chunk_documents_by_line_then_overlap
        texts = ["line content here"]
        result = chunk_documents_by_line_then_overlap(texts)
        assert result[0]["metadata"].get("source") is not None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `E:/Uagent/venv/Scripts/python.exe -m pytest test/unit/test_text_chunker.py::TestChunkDocumentsByLineThenOverlap -v`
Expected: FAIL — `chunk_documents_by_line_then_overlap not defined`

- [ ] **Step 3: 实现函数**

在 `text_chunker.py` 中添加:

```python
def chunk_documents_by_line_then_overlap(
    texts: list[str],
    line_separator: str = "\n",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[dict[str, Any]]:
    """Split text by lines first, then apply overlapping chunking to each line.

    Two-stage chunking:
    1. Split each text by line separator into individual line chunks (no overlap)
    2. For each line chunk, apply overlapping chunking with RecursiveCharacterTextSplitter

    Args:
        texts: List of text strings to chunk.
        line_separator: Separator to split text into lines (default: newline).
        chunk_size: Maximum characters per overlap chunk (applied in stage 2).
        chunk_overlap: Number of overlapping characters between overlap chunks.

    Returns:
        List of chunk dictionaries with 'content' and 'metadata' keys.
    """
    all_chunks: list[dict[str, Any]] = []

    for text in texts:
        # Stage 1: Split by line separator
        lines = text.split(line_separator)

        for line in lines:
            if not line.strip():
                continue

            # Stage 2: Apply overlapping chunking to each line
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            line_docs = splitter.create_documents([line])

            for doc in line_docs:
                chunk_dict = {
                    "content": doc.page_content,
                    "metadata": {"source": ""},  # Will be set by caller
                }
                all_chunks.append(chunk_dict)

    return all_chunks
```

- [ ] **Step 4: 运行测试验证通过**

Run: `E:/Uagent/venv/Scripts/python.exe -m pytest test/unit/test_text_chunker.py::TestChunkDocumentsByLineThenOverlap -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/pipeline/text_chunker.py test/unit/test_text_chunker.py
git commit -m "feat: add chunk_documents_by_line_then_overlap function"
```

---

## Task 3: Pipeline 集成 chunk_method 路由

**Files:**
- Modify: `src/pipeline/run_pipeline.py:55-88` (run_ingestion 方法)

- [ ] **Step 1: 修改 run_ingestion 根据 chunk_method 选择分块函数**

在 `run_pipeline.py` 中:

1. 更新 import 引入新函数:
```python
from src.pipeline.text_chunker import chunk_documents, chunk_documents_by_line_then_overlap
```

2. 修改 `run_ingestion` 中的分块逻辑 (约第77-81行):

```python
# Select chunking function based on config
if self._config.chunk_method == "line_then_overlap":
    chunks = chunk_documents_by_line_then_overlap(
        texts=texts,
        chunk_size=self._config.chunk_size,
        chunk_overlap=self._config.chunk_overlap,
    )
else:
    chunks = chunk_documents(
        texts=texts,
        chunk_size=self._config.chunk_size,
        chunk_overlap=self._config.chunk_overlap,
    )
```

- [ ] **Step 2: 运行现有测试确保没有破坏**

Run: `E:/Uagent/venv/Scripts/python.exe -m pytest test/unit/test_text_chunker.py -v`
Expected: 所有测试 PASS

- [ ] **Step 3: 提交**

```bash
git add src/pipeline/run_pipeline.py
git commit -m "feat: integrate chunk_method config in pipeline"
```

---

## Verification

1. 测试覆盖: `E:/Uagent/venv/Scripts/python.exe -m pytest test/unit/test_text_chunker.py -v --cov=src/pipeline/text_chunker --cov-report=term-missing`
   预期: 关键模块 90%+ 覆盖

2. 手动测试: 使用两种 config 跑 `python run_pipeline.py` 验证分块结果差异

---

## Next Steps

- Option A (recommended): Dispatch subagent-driven-development to execute each task
- Option B: Inline execution via executing-plans skill