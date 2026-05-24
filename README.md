# Uagent RAG 系统

中文文档检索增强生成系统，支持混合搜索（BM25 + 向量检索）、HyDE 查询增强、两阶段重排序和智能上下文选择。

## 系统架构

```
用户查询
     ↓
HyDE Agent（生成假设性文档 + 关键词）
     ↓
         混合检索
         ├── BM25 多关键词聚合
         └── ChromaDB 语义向量检索（HyDE 文档）
     ↓
         RRF 重排序（Reciprocal Rank Fusion，融合 BM25 和向量得分）
     ↓
         CrossEncoder 重排序（Qwen/Qwen3-Reranker-0.6B）
     ↓
         阈值判断上下文选择
         ├── 最大相似度 > threshold 且 gap > gap_threshold → 单块最强
         ├── 平均/中位相似度也高 → 多块合并
         └── 不满足条件 → 重试（最多 n 次，逐步扩大搜索范围）
     ↓
Answer Agent（基于检索上下文生成答案，严格限定知识来源）
```

## 核心特性

- **HyDE（Hypothetical Document Embeddings）**：先让 LLM 生成假设性文档和关键词，再用生成内容检索，缩小查询与文档的语义差距
- **双 LLM 架构**：HyDE 使用 qwen3.5-4b（高温度，创造性生成），RAG 使用 lfm2-1b-rag（低温度，严格忠实于上下文）
- **两阶段重排序**：RRF（Reciprocal Rank Fusion）融合 BM25 和向量检索结果 → CrossEncoder 精细排序
- **动态检索结果**：根据相似度分数动态选择单块或多块检索块，失败重试机制
- **DeepEval 评估**： AnswerRelevancy、ContextualPrecision、ContextualRecall

## 环境要求

- Python 3.10+
- OpenAI 兼容的 LLM 服务（如 LM Studio、vLLM）
- OpenAI 兼容的 Embedding 服务
- 本地 HuggingFace 模型：`Qwen/Qwen3-Reranker-0.6B`




## 使用指南

### 索引文档

支持两种输入格式：

**普通文本文件（.txt/.md）：**
```python
from src.pipeline.pipe import Pipeline

pipeline = Pipeline()
pipeline.execute("./inputs", mode="plain")
```

**JSONL 格式（每行一个 JSON 对象，含 context 字段）：**
```python
pipeline = Pipeline()
pipeline.execute("./inputs", mode="jsonl")
```

索引数据保存到 `./chroma_db`，包括：
- ChromaDB 向量存储
- BM25 索引文件

### 单次查询

```python
from src.chain import chain_pipeline

chain = chain_pipeline()
answer, contexts = chain.execute("你的查询问题")
print(answer)
```

### QA 检索生成

```python
# 修改 main.py 中的参数后运行：
# N_SAMPLE = 140  # 评估样本数
# K_RETRIEVAL = 3  # 检索数量
# THESHOLD = 0.8   # 相似度阈值
cd e:\Uagent && venv\Scripts\python main.py
```

## 配置说明

所有配置位于 `src/config.py`：

| 配置类 | 参数 | 说明 |
|--------|------|------|
| `LlmConfig` | model_name="qwen3.5-4b", temperature=0.8 | 基础 LLM 配置 |
| `HyDEConfig` | model_name="qwen3.5-4b", temperature=0.75 | HyDE 生成 LLM（高温度，鼓励创造性） |
| `RAGConfig` | model_name="lfm2-1b-rag", temperature=0.05 | 回答生成 LLM（低温度，严格忠实） |
| `EmbedModelConfig` | model="text-embedding-qwen3-embedding-0.6b", dims=1024 | Embedding 模型 |
| `IndexConfig` | chunk_size=600, chunk_overlap=60, dir="./chroma_db" | 索引参数 |

## 项目文件

| 文件 | 说明 |
|------|------|
| `src/chain.py` | 主流程：HyDE → 混合检索 → RRF → CrossEncoder → 阈值选择 → 回答 |
| `src/config.py` | 所有配置类定义 |
| `src/pipeline/pipe.py` | 文档索引管道（分块 → 向量化 → ChromaDB 存储 → BM25 索引）|
| `src/model/llm.py` | LLM 调用封装（ChatOpenAI） |
| `src/model/embedm.py` | Embedding 模型封装（OpenAIEmbeddings），含文本清洗 |
| `src/chunker/line_splitter.py` | 行级文本分块器 |
| `src/chunker/jsonl_splitter.py` | JSONL 文档分块器 |
| `src/utils/bm25.py` | BM25 检索器（jieba 分词（未使用），支持 ChromaDB 集成、索引保存/加载）|
| `src/utils/hash.py` | SHA256 哈希工具 |
| `main.py` | 检索生成 |
| `embed_demo.py` | 生成索引 |
| `extract_datasets.py` | SQuAD v2.0 JSON → JSONL 数据集提取工具 |
| `tests/evals/metrics.py` | DeepEval 评估指标定义 |
| `tests/evals/smoke_test.py` | 单条 QA 冒烟测试 |
| `tests/evals/test_in_code.py` | 批量 DeepEval 评估 |
| `example/BM25_eg.py` | BM25 使用示例 |
| `example/deepeval_eg.py` | DeepEval 评估示例 |
| `test/unit/test_bm25.py` | BM25 单元测试 |

## 评估

使用 DeepEval 框架进行 RAG 质量评估：

```bash
# 1. 运行检索生成结果
venv\Scripts\python main.py

# 2. 批量评估（ContextualPrecision + ContextualRecall + AnswerRelevancy）
venv\Scripts\python tests/evals/test_in_code.py

# 3. 单条冒烟测试
venv\Scripts\python tests/evals/smoke_test.py
```

## 数据集

`extract_datasets.py` 从 SQuAD v2.0 JSON 格式提取：
- `inputs/contexts.jsonl` — 文档原文（去重）
- `inputs/qa_pairs.jsonl` — 问答对（含无答案问题）
  
## 模型
- Qwen3.5 4B Q4_K_M
- Qwen3 Embedding 0.6B Q8
- LFM2 1B RAG
- CompassJudger 7B It Q4_K_M