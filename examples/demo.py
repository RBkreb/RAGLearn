#!/usr/bin/env python3
"""Q&A 系统演示程序.

展示三种前缀模式的使用:
- /btw - 直接回答，无记忆
- /base - 基于上下文回答
- 无前缀 - 使用默认配置行为

数学计算示例:
- 5 + 3
- 10 * 5
- 20 / 4
- 100 - 37
"""

from src.chain import QAChain


def print_separator() -> None:
    """打印分隔线."""
    print("=" * 50)


def main() -> None:
    """主函数."""
    chain = QAChain()

    print("Q&A 系统演示")
    print_separator()
    print("输入问题，或使用以下前缀：")
    print("  /btw <问题>  - 直接回答，无记忆")
    print("  /base <问题> - 基于上下文回答")
    print("  quit - 退出")
    print_separator()
    print("\n数学计算示例：")
    print("  5 + 3")
    print("  10 * 5")
    print("  20 / 4")
    print("  100 - 37")
    print_separator()

    while True:
        try:
            query = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if query.lower() in ("quit", "exit", "q"):
            print("再见！")
            break

        if not query:
            continue

        print_separator()
        response = chain.invoke(query)
        print(f"AI: {response}")
        print_separator()


if __name__ == "__main__":
    main()