# Q&A 问答系统

基于 LangChain 和 OpenAI 兼容接口的本地问答系统，支持前缀路由和对话记忆。

## 功能特性

- **前缀路由**：通过前缀决定回答模式
  - `/btw` - 直接回答，无记忆
  - `/base` - 基于上下文回答，保留对话历史
  - 无前缀 - 使用配置文件中的默认行为

- **LangChain Memory**：使用 `ChatMessageHistory` 实现短时对话记忆
- **本地 LLM**：使用 OpenAI 兼容接口的本地模型（如 LM Studio / Ollama）
- **RAG 检索**：基于 ChromaDB 的向量检索，支持文档知识库问答
- **配置灵活**：通过 `config.py` 自定义默认行为和 LLM 参数

## 系统要求

- Python 3.12+
- 本地 LLM 服务运行于 `http://127.0.0.1:1234`
- 模型已加载（兼容 OpenAI API 格式）



1. 确保本地 LLM 服务运行中

## 使用方法

### 交互式演示

```bash
python examples/demo.py
```

### 代码示例

```python
from src import QAChain

chain = QAChain()

# /btw 前缀 - 直接回答，无记忆
response = chain.invoke("/btw 什么是 TCP?")
print(response)

# /base 前缀 - 使用对话上下文
response = chain.invoke("/base 那 UDP 呢？")
print(response)

# 无前缀 - 使用默认配置行为
response = chain.invoke("它们有什么区别？")
print(response)

# 清除对话记忆
chain.clear_memory()
```

## 配置

编辑 `src/config.py` 修改默认行为：

```python
from src.config import DefaultModeConfig, LLMConfig

# 默认模式配置
default_mode = DefaultModeConfig(
    mode="base",  # "direct" 或 "base"
    temperature=0.7,
    max_tokens=1024
)

# LLM 配置 (OpenAI 兼容接口)
llm_config = LLMConfig(
    model="qwen3.5",
    base_url="http://127.0.0.1:1234/v1",
    api_key="no-key",
    temperature=0.7,
    max_tokens=1024
)
```

## 项目结构

```
E:\Uagent\
├── src/                    # 源代码
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── router.py          # 前缀路由解析
│   ├── memory_manager.py   # 对话记忆管理
│   ├── llm_service.py     # LLM 调用服务
│   ├── chain.py            # 主链编排
│   ├── pipeline/           # RAG 管道
│   │   ├── document_loader.py
│   │   ├── text_chunker.py
│   │   ├── embedding_service.py
│   │   ├── vector_store.py
│   │   └── run_pipeline.py
│   └── tools/
│       ├── rag_tool.py    # RAG 检索工具
│       └── math_tools.py
├── examples/
│   └── demo.py            # 交互式演示
├── test/
│   └── unit/              # 单元测试
├── model/                  # LLM 模型文件
├── chroma_db/            # 向量数据库
├── embed_demo.py         # RAG 管道演示
└── README.md
```

## 测试

运行单元测试：

```bash
python -m pytest test/unit/ -v
```

查看覆盖率：

```bash
python -m pytest test/unit/ --cov=src --cov-report=term-missing
```

## 核心模块

| 模块 | 说明 |
|------|------|
| `config.py` | 全局配置管理 |
| `router.py` | 前缀解析，`QueryParser` 识别 `/btw`、`/base` |
| `memory_manager.py` | `MemoryManager` 使用 `ChatMessageHistory` |
| `llm_service.py` | `LLMService` 调用 `ChatOpenAI`（OpenAI 兼容接口） |
| `chain.py` | `QAChain` 编排路由、记忆、LLM |

