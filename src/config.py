"""Configuration management for Q&A system."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class DefaultModeConfig(BaseModel):
    """Default mode configuration.

    Attributes:
        mode: Default routing mode - "base" or "direct". Currently only "direct" is used.
        temperature: LLM sampling temperature.
        max_tokens: Maximum tokens to generate.
    """

    mode: Literal["base", "direct"] = Field(default="direct")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=1024)


class LLMConfig(BaseModel):
    """LLM configuration for ChatOpenAI (compatible with local LLM servers).

    Attributes:
        model: Model name (e.g., "qwen3.5").
        temperature: Sampling temperature.
        max_tokens: Maximum tokens to generate.
        base_url: Base URL of the LLM server.
        api_key: API key for authentication (default: "no-key").
    """

    model: str = Field(default="qwen3.5")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=1024)
    base_url: str = Field(default="http://127.0.0.1:1234/v1")
    api_key: str = Field(default="no-key")


class AgentConfig(BaseModel):
    """Agent configuration for tool-enabled LLM.

    Attributes:
        system_prompt: System prompt for the agent with math tools.
        tools: List of tool names to bind to the agent.
    """

    system_prompt: str = Field(
        default="""你是一个知识问答助手。
当用户询问关于文档、规范、定义、规格等具体信息时，必须使用 rag_retrieve 工具从知识库检索相关信息。
知识库中包含一个虚构世界的设定集
优先使用 rag_retrieve 回答涉及知识、概念、定义的问题。
如果知识库中没有相关知识，则直接回答不知道"""
    )
    tools: list[str] = Field(
        #default=["rag_retrieve", "add", "subtract", "multiply", "divide"],
        default=["rag_retrieve"],
        description="List of tool names to bind to the agent",
    )


class PipelineConfig(BaseModel):
    """Pipeline configuration for RAG ingestion.

    Attributes:
        input_dir: Directory containing input documents.
        chroma_db_path: Path for ChromaDB persistence.
        embedding_model_path: Path to GGUF embedding model.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Overlapping characters between chunks.
        top_k: Number of documents to retrieve.
        embedding_n_ctx: Context size for embedding model.
        embedding_n_threads: Number of threads for inference.
        embedding_n_batch: Batch size for embedding inference.
        collection_name: ChromaDB collection name.
    """

    input_dir: Path = Field(default=Path("input"))
    chroma_db_path: str = Field(default="./chroma_db")
    embedding_model_path: str = Field(
        default="model/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"
    )
    chunk_size: int = Field(default=500)
    chunk_overlap: int = Field(default=90)
    chunk_method: Literal["overlap", "line_then_overlap"] = Field(
        default="overlap",
        description="Chunking method: 'overlap' uses traditional overlapping chunks, "
                    "'line_then_overlap' splits by lines first then applies overlap chunking to each line",
    )
    top_k: int = Field(default=4)
    embedding_n_ctx: int = Field(default=1024)
    embedding_n_threads: int = Field(default=4)
    embedding_n_batch: int = Field(default=4)
    collection_name: str = Field(default="documents")


class Config(BaseModel):
    """Global configuration container.

    Attributes:
        default_mode: Default behavior for queries without prefix.
        llm: LLM configuration.
        agent: Agent configuration for tool-enabled LLM.
        pipeline: Pipeline configuration for RAG ingestion.
    """

    default_mode: DefaultModeConfig = Field(default_factory=DefaultModeConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)


# Global configuration instance
_config: Config | None = None


def get_config() -> Config:
    """Get global configuration instance.

    Returns:
        Global Config instance.
    """
    global _config
    if _config is None:
        _config = Config()
    return _config