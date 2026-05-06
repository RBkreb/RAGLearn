"""Configuration dataclasses for RAG Q&A bot."""

from dataclasses import dataclass, field


@dataclass
class LlamaCppConfig:
    """Configuration for LlamaCpp LLM and embedding models."""

    model_path: str = "./model/Qwen3.5-0.8B-GGUF/Qwen3.5-0.8B-Q8_0.gguf"
    embedding_model_path: str = "./model/Qwen3-Embedding-4B-GGUF/Qwen3-Embedding-4B-Q4_K_M.gguf"
    temperature: float = 0.15
    n_gpu_layers: int = -1
    n_ctx: int = 8192
    max_tokens: int = 2048
    timeout: int = 120


@dataclass
class IndexConfig:
    """Configuration for document indexing."""

    chunk_size: int = 600
    chunk_overlap: int = 60
    persist_directory: str = "./chroma_db"


DEFAULT_PROMPT_TEMPLATE = """

Context:
{context}

Question: {question}

回答规则
- 不要复述或评价参考资料中不存在的内容
- 回答要简洁、直接

"""


@dataclass
class PromptConfig:
    """Configuration for RAG prompt templates."""

    template: str = DEFAULT_PROMPT_TEMPLATE
    system_prompt: str = '''你是一个严格的助手。只使用用户提供的参考资料回答问题,不编造、不联想。信息不足时只回复:无法确定。'''


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline."""

    llamacpp: LlamaCppConfig = field(default_factory=LlamaCppConfig)
    index: IndexConfig = field(default_factory=IndexConfig)
    prompt: PromptConfig = field(default_factory=PromptConfig)
    top_k: int = 3
    enable_graph: bool = False