#!/usr/bin/env python3
"""RAG Q&A Bot 示例程序。

此程序演示如何使用 RAG 管道进行文档索引和查询。
"""
import warnings
warnings.filterwarnings("ignore", message=".*embeddings required but some input tokens.*")

from src.pipeline import build_pipeline, load_pipeline
from src.config import RAGConfig, LlamaCppConfig


def main() -> None:
    """运行 RAG 示例程序."""
    config = RAGConfig(llamacpp=LlamaCppConfig())

    print("=" * 60)
    print("RAG Q&A Bot 示例程序")
    print("=" * 60)

    print("\n[1] 构建 RAG 管道...")
    pipeline = build_pipeline(config)
    print("    管道构建完成")

    print("\n[2] 索引 input/ 目录中的文档...")
    stats = pipeline.index_documents('input/')
    print(f"    已索引: {stats.documents_processed} 个文档")
    print(f"    已创建: {stats.chunks_created} 个块")
    print(f"    已处理: {stats.batches_processed} 个批次")

    print("\n[3] 查询示例问题...")
    questions = [
        "什么是 OSI 模型?",
        "解释应用层的作用",
    ]

    for question in questions:
        print(f"\n    问题: {question}")
        result = pipeline.query_with_sources(question)
        print(f"    答案: {result.answer}")
        print(f"    来源: {result.sources}")

    print("\n" + "=" * 60)
    print("示例程序结束")
    print("=" * 60)


def query_only() -> None:
    """仅查询模式 - 从已持久化的索引加载."""
    config = RAGConfig(llamacpp=LlamaCppConfig())

    print("=" * 60)
    print("RAG Q&A Bot (仅查询模式)")
    print("=" * 60)

    print("\n[1] 从持久化索引加载 RAG 管道...")
    pipeline = load_pipeline(config)
    print("    加载完成")

    print("\n[2] 输入问题 (输入 'quit' 退出)...")

    while True:
        question = input("\n问题: ").strip()
        if question.lower() == 'quit':
            break
        if not question:
            continue

        result = pipeline.query_with_sources(question)
        print(f"\n答案: {result.answer}")
        if result.sources:
            print(f"来源: {result.sources}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--query":
        query_only()
    else:
        main()
