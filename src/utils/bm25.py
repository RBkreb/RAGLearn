"""BM25 retriever for ChromaDB documents."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import jieba
from bm25s import BM25
from bm25s.tokenization import Tokenized
from langchain_core.documents import Document
from chromadb import Collection
if TYPE_CHECKING:
    from langchain_chroma import Chroma


def tokenize(
    texts: str | list[str],
    return_ids: bool = True,
    show_progress: bool = False,
) -> Tokenized:
    """Tokenize texts using jieba Chinese segmentation.

    Args:
        texts: Single text or list of texts.
        return_ids: If True, return token IDs; otherwise return token strings.
        show_progress: Show progress bar.

    Returns:
        Tokenized object with corpus IDs and vocabulary.
    """
    if isinstance(texts, str):
        texts = [texts]

    corpus_ids: list[list[int]] = []
    token_to_index: dict[str, int] = {}

    for text in texts:
        tokens = jieba.lcut(text)
        doc_ids: list[int] = []

        for token in tokens:
            if token not in token_to_index:
                token_to_index[token] = len(token_to_index)
            doc_ids.append(token_to_index[token])

        corpus_ids.append(doc_ids)

    return Tokenized(ids=corpus_ids, vocab=token_to_index)


BM25.tokenize = tokenize  # type: ignore[attr-defined]


class BM25Retriever:
    """BM25 retriever for document search."""

    def __init__(self, corpus: list[str] | None = None) -> None:
        """Initialize BM25 retriever.

        Args:
            corpus: Optional initial corpus for indexing.
        """
        self._corpus: list[str] = corpus if corpus is not None else []
        self._retriever: BM25 | None = None
        self._chroma_client: Chroma | None = None
        self._collection_name: str = "collection"

    def set_chroma(
        self,
        chroma_client: Chroma,
        collection_name: str = "collection",
    ) -> None:
        """Set ChromaDB client for document retrieval.

        Args:
            chroma_client: ChromaDB client instance.
            collection_name: Name of the collection to use.
        """
        self._chroma_client = chroma_client
        self._collection_name = collection_name

    def index(self, corpus: list[str] | None = None) -> None:
        """Build BM25 index from corpus.

        Args:
            corpus: Corpus to index. Uses stored corpus if None.
        """
        target_corpus = corpus if corpus is not None else self._corpus
        if not target_corpus:
            raise ValueError("No corpus provided for indexing")

        self._corpus = target_corpus
        corpus_tokens = tokenize(target_corpus)
        self._retriever = BM25(corpus=target_corpus)
        self._retriever.index(corpus_tokens)

    def index_from_chroma(
        self,
        chroma_client: Chroma | None = None,
        #collection_name: str | None = None,
    ) -> None:
        """Build BM25 index from ChromaDB collection.

        Args:
            chroma_client: ChromaDB client. Uses stored client if None.
            collection_name: Collection name. Uses stored name if None.
        """
        client = chroma_client if chroma_client is not None else self._chroma_client
        if client is None:
            raise ValueError("No ChromaDB client provided")

        #collection_nm = collection_name if collection_name is not None else self._collection_name
        collection:Collection = client._collection

        docs:Document = collection.get()
        self._corpus = docs["documents"]
        self.index()

    def save(self, path: str) -> None:
        """Save BM25 index to disk.

        Args:
            path: Directory path to save index files.
        """
        if self._retriever is None:
            raise ValueError("No index to save. Call index() first.")

        import os

        os.makedirs(path, exist_ok=True)
        self._retriever.save(path)

        corpus_path = os.path.join(path, "corpus.txt")
        with open(corpus_path, "w", encoding="utf-8") as f:
            for doc in self._corpus:
                f.write(doc + "\n")

    @classmethod
    def load(
        cls,
        path: str,
        corpus: list[str] | None = None,
    ) -> BM25Retriever:
        """Load BM25 index from disk.

        Args:
            path: Directory path containing index files.
            corpus: Optional corpus override. If None, loads from corpus.txt.

        Returns:
            BM25Retriever instance with loaded index.
        """
        import os

        retriever = cls()

        corpus_path = os.path.join(path, "corpus.txt")
        if corpus is not None:
            retriever._corpus = corpus
        elif os.path.exists(corpus_path):
            with open(corpus_path, "r", encoding="utf-8") as f:
                retriever._corpus = [line.strip() for line in f if line.strip()]
        else:
            raise ValueError("No corpus available. Provide corpus or ensure corpus.txt exists.")

        loaded_retriever = BM25.load(path)
        retriever._retriever = loaded_retriever

        # bm25s BM25.load does not restore corpus, set it manually
        retriever._retriever.corpus = retriever._corpus

        return retriever

    def retrieve(
        self,
        query: str,
        k: int = 5,
    ) -> tuple[list[str], list[float]]:
        """Search documents using BM25.

        Args:
            query: Query string.
            k: Number of results to return.

        Returns:
            Tuple of (document list, score list).
        """
        if self._retriever is None:
            raise ValueError("No index. Call index() or index_from_chroma() first.")

        query_tokens = tokenize(query)
        docs, scores = self._retriever.retrieve(query_tokens, k=k)

        return docs[0].tolist(), scores[0].tolist()