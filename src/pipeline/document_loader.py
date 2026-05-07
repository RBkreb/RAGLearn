"""Document loader for pipeline."""

from pathlib import Path
from typing import Iterator


def load_documents(input_dir: Path) -> Iterator[tuple[str, str]]:
    """Load .md and .txt files from input directory.

    Args:
        input_dir: Directory to load documents from.

    Yields:
        Tuples of (filepath, content).

    Raises:
        ValueError: If input_dir is not a valid directory.
    """
    if not input_dir.is_dir():
        raise ValueError(f"Input directory does not exist: {input_dir}")

    for filepath in input_dir.iterdir():
        if filepath.suffix.lower() in (".md", ".txt"):
            content = filepath.read_text(encoding="utf-8")
            yield (str(filepath), content)
