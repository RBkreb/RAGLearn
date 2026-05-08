"""清洗MD文件：去除图片引用和HTML表格标签"""
import re
import shutil
from pathlib import Path


def clean_md_content(content: str) -> str:
    """去除MD文件中的图片引用和HTML标签

    Args:
        content: 原始文件内容

    Returns:
        清洗后的内容
    """
    # 去除图片引用 ![...](...)
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)

    # 去除HTML表格相关标签
    content = re.sub(r'</?table[^>]*>', '', content)
    content = re.sub(r'</?tr[^>]*>', '', content)
    content = re.sub(r'</?td[^>]*>', '', content)
    content = re.sub(r'</?th[^>]*>', '', content)
    content = re.sub(r'</?tbody[^>]*>', '', content)
    content = re.sub(r'</?thead[^>]*>', '', content)

    # 去除HTML换行和div标签
    content = re.sub(r'<br\s*/?>', '', content)
    content = re.sub(r'</?div[^>]*>', '', content)

    # 清理多余的空行（多个连续空行合并为一个）
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content.strip()


def process_file(file_path: Path) -> None:
    """处理单个MD文件

    Args:
        file_path: 文件路径
    """
    if not file_path.exists() or file_path.suffix != '.md':
        return

    # 读取原文件
    content = file_path.read_text(encoding='utf-8')

    # 备份原文件
    bak_path = file_path.with_suffix(file_path.suffix + '.bak')
    shutil.copy2(file_path, bak_path)

    # 清洗内容并写回
    cleaned = clean_md_content(content)
    file_path.write_text(cleaned, encoding='utf-8')

    print(f"已处理: {file_path.name} -> 备份: {bak_path.name}")


def main() -> None:
    """主函数"""
    input_dir = Path(__file__).parent / 'input'

    md_files = list(input_dir.glob('*.md'))
    print(f"找到 {len(md_files)} 个MD文件")

    for md_file in md_files:
        process_file(md_file)

    print("完成!")


if __name__ == '__main__':
    main()