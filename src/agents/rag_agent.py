"""RAG agent module using LangChain."""

from typing import Any, NamedTuple

from langchain_core.documents import Document as LCDocument

from src.models.llm import LlamaCppLLMWrapper
from src.retrieval.hybrid_retriever import HybridRetriever, RetrievalResult


class AnswerResult(NamedTuple):
    """Immutable answer result container.

    Attributes:
        answer: The generated answer text.
        sources: List of source documents used.
        scores: List of relevance scores.
    """

    answer: str
    sources: list[str]
    scores: list[float]
    metadata: dict[str, Any] | None = None


class RAGAgent:
    """RAG agent combining retrieval and generation.

    This class handles retrieving relevant context and generating
    answers using the LLM.

    Attributes:
        retriever: Hybrid retriever for document retrieval.
        llm: Ollama LLM wrapper for generation.
        prompt_config: Prompt configuration for RAG.
    """

    def __init__(
        self,
        retriever: HybridRetriever,
        llm: LlamaCppLLMWrapper,
        prompt_template: str | None = None,
        system_prompt: str | None = None,
    ) -> None:
        """Initialize RAGAgent.

        Args:
            retriever: Hybrid retriever for document retrieval.
            llm: Ollama LLM wrapper for answer generation.
            prompt_template: Optional prompt template with {context} and {question} placeholders.
            system_prompt: Optional system prompt.
        """
        from src.config import DEFAULT_PROMPT_TEMPLATE

        self.retriever = retriever
        self.llm = llm
        self.prompt_template = prompt_template or DEFAULT_PROMPT_TEMPLATE
        self.system_prompt = system_prompt or ""

    def ask(self, question: str) -> str:
        """Ask a question and get an answer.

        Args:
            question: The user's question.

        Returns:
            The generated answer as a string.
        """
        result = self.ask_with_sources(question)
        return result.answer

    def ask_with_sources(self, question: str) -> AnswerResult:
        """Ask a question and get an answer with sources.

        Args:
            question: The user's question.

        Returns:
            AnswerResult with answer, sources, and scores.
        """
        retrieval_results = self.retriever.retrieve(question)

        context_parts = []
        sources: list[str] = []
        scores: list[float] = []

        for r in retrieval_results:
            context_parts.append(r.content)
            sources.append(r.source)
            scores.append(r.distance)

        context = "\n\n".join(context_parts)

        prompt = self.prompt_template.format(context=context, question=question)

        answer = self.llm.invoke(prompt)

        return AnswerResult(
            answer=answer,
            sources=sources,
            scores=scores,
            metadata={
                "retrieval_count": len(retrieval_results),
                "question": question,
            },
        )

    def format_sources(self, result: AnswerResult) -> str:
        """Format sources into a readable string.

        Args:
            result: The answer result to format.

        Returns:
            Formatted string with sources and scores.
        """
        lines = ["Sources:"]
        for i, (source, score) in enumerate(zip(result.sources, result.scores)):
            lines.append(f"  {i + 1}. {source} (score: {score:.4f})")
        return "\n".join(lines)