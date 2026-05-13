# QAbot 问答系统

基于 LangChain v1 中间件钩子的智能问答系统，支持前缀路由、对话记忆和安全检查。

## 功能特性

- **LangChain v1 中间件钩子**：使用 `@before_agent`、`@before_model`、`@after_model`、`@after_agent` 等钩子分离关注点
- **安全检查**：在 `@before_agent` 阶段拦截危险指令和提示注入攻击
- **意图路由**：自动检测数学计算意图，动态切换 system prompt 和工具
- **动态工具注入**：MATH 意图时自动注入数学工具（加减乘除）
- **自动摘要**：对话过长时触发异步摘要，减少 token 消耗
- **会话管理**：支持多会话切换、记忆持久化和上下文恢复

## 系统要求

- Python 3.12+
- 本地 LLM 服务运行于 `http://127.0.0.1:1234`
- 模型已加载（兼容 OpenAI API 格式）

## 项目结构

```
E:\Uagent\
├── src/
│   ├── agent/
│   │   ├── conversation_agent.py  # 对话 Agent（使用 middleware 钩子）
│   │   └── middleware.py          # LangChain v1 中间件实现
│   ├── intent_router.py           # 意图检测（MATH/NORMAL）
│   ├── safety_checker.py          # 安全检查
│   ├── short_term_memory.py       # 短时记忆
│   ├── long_term_memory.py        # 长时记忆（会话摘要存储）
│   ├── session_manager.py         # 会话管理
│   ├── summarizer.py              # 异步摘要
│   ├── cli.py                     # 命令行界面
│   └── tools/
│       ├── math_tools.py          # 数学工具
│       └── rag_tool.py            # RAG 检索工具
├── test/
│   ├── unit/                      # 单元测试
│   └── integration/                # 集成测试
├── chroma_db/                     # 向量数据库（不跟踪）
├── sessions/                     # 会话数据（不跟踪）
└── README.md
```

## 中间件架构

| 中间件 | 钩子 | 职责 |
|--------|------|------|
| `SafetyCheckMiddleware` | `@before_agent` | 安全检查 + 意图检测，危险输入短路 |
| `PromptContextMiddleware` | `@before_model` | 根据 intent 注入 system prompt 和工具描述 |
| `UsageTrackingMiddleware` | `@wrap_model_call` + `@after_model` | Token 统计 |
| `AutoSummarizeMiddleware` | `@after_agent` | 检查 token 阈值，触发异步摘要 |

## 使用方法

### 交互式对话

```bash
python -m src.cli
```

### 代码示例

```python
from src.agent.conversation_agent import ConversationAgent
from src.short_term_memory import ShortTermMemory

# 创建记忆
memory = ShortTermMemory(session_id="test-session")

# 创建 Agent（需要提供 LLM callable）
agent = ConversationAgent(llm_callable=llm_func, short_term_memory=memory)

# 处理用户输入
response = agent.process("计算 123+456")
print(response)

# 操控记忆
agent.rewind(1)      # 回退一步
agent.compact("摘要") # 压缩记忆
```

### CLI 命令

- `/new [session_name]` - 创建新会话
- `/switch <session_id>` - 切换会话
- `/sessions` - 列出所有会话
- `/rewind [n]` - 回退 n 步
- `/repeat` - 重复上一个回答
- `/compact <summary>` - 压缩记忆
- `/quit` - 退出

## 测试

```bash
# 运行所有测试
python -m pytest test/ -v

# 运行单元测试
python -m pytest test/unit/ -v

# 运行集成测试
python -m pytest test/integration/ -v

# 查看覆盖率
python -m pytest test/ --cov=src --cov-report=term-missing
```

## 核心模块

| 模块 | 说明 |
|------|------|
| `agent/conversation_agent.py` | 对话 Agent，使用 `create_agent` + middleware |
| `agent/middleware.py` | 四个中间件实现（Safety, Prompt, Usage, Summarize） |
| `intent_router.py` | `IntentRouter` 检测 MATH/NORMAL 意图 |
| `safety_checker.py` | `SafetyChecker` 拦截危险指令和注入攻击 |
| `short_term_memory.py` | `ShortTermMemory` 管理单会话对话历史 |
| `session_manager.py` | `SessionManager` 管理多会话持久化 |