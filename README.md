# RAG Q&A Bot

基于 LangChain  的 RAG (检索增强生成) 问答机器人。

## 功能特性

- **文档索引**: 支持 MD 文档解析和分块
- **向量检索**: ChromaDB 持久化存储
- **混合检索**: 基于语义相似度的文档检索
- **流式批处理**: 内存优化的批量索引
- **内存监控**: 内置内存泄漏检测

## 项目结构

```
src/
├── config.py              # 配置 dataclasses
├── pipeline.py            # RAG 管道编排
├── exceptions.py           # 自定义异常
├── models/
│   ├── llm.py            # llama-cpp-python LLM 封装
│   └── embedding.py      # llama-cpp-python Embedding 封装
├── indexing/
│   ├── parser.py         # 文档解析器
│   ├── chunker.py        # 文本分块器
│   └── vector_index.py   # ChromaDB 索引管理器
├── retrieval/
│   └── hybrid_retriever.py  # 混合检索器
├── agents/
│   └── rag_agent.py      # RAG Agent
└── monitoring/
    └── memory_monitor.py # 内存监控
```

## 快速开始

### 前提条件

- Python 虚拟环境: `E:/Uagent/venv/Scripts/python.exe`
- llama-cpp-python安装
- 已部署模型:
  - `qwen3.5:0.8b` (Chat LLM)
  - `qwen3-embedding:4b` (Embedding)

### 运行示例程序

```bash
# 完整示例 (索引 + 查询)
E:/Uagent/venv/Scripts/python.exe main.py

# 仅查询模式 (从已持久化索引加载)
E:/Uagent/venv/Scripts/python.exe main.py --query
```


## 运行测试

```bash
# 所有单元测试
E:/Uagent/venv/Scripts/python.exe -m pytest test/unit/ -v

# 带覆盖率
E:/Uagent/venv/Scripts/python.exe -m pytest test/unit/ --cov=src --cov-report=term-missing
```

## 配置说明

### RAGConfig

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `llamacpp.model_path` | `./model/Qwen3.5-0.8B-GGUF/Qwen3.5-0.8B-Q8_0.gguf` | Chat 模型路径 |
| `llamacpp.embedding_model_path` | `./model/Qwen3-Embedding-4B-GGUF/Qwen3-Embedding-4B-Q4_K_M.gguf` | Embedding 模型路径 |
| `llamacpp.temperature` | `0.15` | 生成温度 |
| `llamacpp.n_ctx` | `12288` | 上下文窗口大小 |
| `llamacpp.max_tokens` | `2048` | 最大输出 token 数 |
| `index.chunk_size` | `600` | 分块大小 |
| `index.chunk_overlap` | `60` | 分块重叠 |
| `index.persist_directory` | `./chroma_db` | ChromaDB 持久化目录 |
| `prompt.template` | 见 `DEFAULT_PROMPT_TEMPLATE` | RAG 提示模板 |
| `prompt.system_prompt` | `You are a helpful AI assistant.` | 系统提示词 |
| `top_k` | `3` | 检索返回数量 |

## 数据流程

```
输入文档 → Parser → Chunker → Embedding → ChromaDB
                                              ↓
用户问题 → Embedding → HybridRetriever → RAGAgent → ChatLlamaCpp → 答案
```
