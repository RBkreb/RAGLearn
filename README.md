# Uagent RAG 系统

中文文档检索增强生成系统，支持混合搜索（BM25 + 向量检索）和 HyDE 查询增强。

## 系统架构

```
用户查询 → HyDE Agent（生成假设性文档 + 关键词）
              ↓
         混合检索
         ├── BM25（jieba 中文分词）
         └── ChromaDB 向量检索
              ↓
         RFF 重排序（合并 BM25 和向量得分）
              ↓
         Answer Agent（基于上下文生成答案）
```

## 环境要求

- Python 3.10+
- OpenAI 兼容的 LLM 服务
- OpenAI 兼容的 Embedding 服务

## 索引建立示例

```python
from src.pipeline.pipe import Pipeline

# 创建管道并执行索引
pipeline = Pipeline()
pipeline.execute("inputs/documents.txt")
```


索引数据会保存到 `./chroma_db` 目录，包括：
- ChromaDB 向量存储
- BM25 索引文件

## 单次对话示例

```python
from src.chain import chain_pipeline

# 初始化 chain（加载索引）
pipeline = chain_pipeline()

# 执行查询
response = pipeline.execute("What is your mission in shanghai?")
print(response)
```



## 核心配置 (src/config.py)

| 配置项 | 值 |
|--------|-----|
| LLM 模型 | qwen3.5-0.8b |
| LLM 地址 | http://127.0.0.1:1234/v1 |
| Embedding 模型 | text-embedding-qwen3-embedding-0.6b |
| Embedding 维度 | 1024 |
| 块大小 | 600 字符 |
| 块重叠 | 60 字符 |
| 向量库路径 | ./chroma_db |

## 关键文件

| 文件 | 说明 |
|------|------|
| `src/chain.py` | 主流程：HyDE → 混合检索 → 重排 → 回答 |
| `src/pipeline/pipe.py` | 文档索引管道（分词 → 向量化 → 存储）|
| `src/model/llm.py` | LLM 调用封装 |
| `src/model/embedm.py` | Embedding 模型封装 |
| `src/utils/bm25.py` | BM25 检索器（jieba 分词）|
| `src/utils/hash.py` | 文档内容 SHA256 哈希 |

