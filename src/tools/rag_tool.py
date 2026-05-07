"""RAG tool for retrieving context from vector database."""

from langchain_core.tools import tool

_retriever = None


def set_retriever(retriever) -> None:
    """Set global retriever for RAG tool.

    Args:
        retriever: LangChain retriever instance.
    """
    global _retriever
    _retriever = retriever


@tool("rag_retrieve", description="""Search document knowledge base for relevant information.
Use when user asks about specific information from documents, definitions, specifications.
Input: search query string.
Output: relevant context chunks with source attribution.""")
def rag_retrieve(query: str) -> str:
    """Search vector database for relevant context.

    Args:
        query: Search query string.

    Returns:
        Formatted context chunks or error message.
    """
    if _retriever is None:
        return "Error: RAG retriever not initialized."
    docs = _retriever.invoke(query)
    if not docs:
        return "No relevant information found."
    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown")
        formatted.append(f"[Chunk {i}] (Source: {source})\n{doc.page_content}")
    return "\n\n---\n\n".join(formatted)
