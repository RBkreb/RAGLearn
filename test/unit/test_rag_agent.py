"""Unit tests for RAG agent module."""

from unittest.mock import MagicMock

import pytest

from src.agents.rag_agent import AnswerResult, RAGAgent
from src.retrieval.hybrid_retriever import RetrievalResult


class TestAnswerResult:
    """Tests for AnswerResult NamedTuple."""

    def test_answer_result_has_expected_fields(self):
        """AnswerResult should have answer, sources, scores, metadata fields."""
        result = AnswerResult(
            answer="test answer",
            sources=["source1", "source2"],
            scores=[0.9, 0.8],
            metadata={"key": "value"},
        )
        assert result.answer == "test answer"
        assert result.sources == ["source1", "source2"]
        assert result.scores == [0.9, 0.8]
        assert result.metadata == {"key": "value"}

    def test_answer_result_metadata_defaults_to_none(self):
        """AnswerResult metadata should default to None."""
        result = AnswerResult(
            answer="test answer",
            sources=["source1"],
            scores=[0.9],
        )
        assert result.metadata is None

    def test_answer_result_is_immutable(self):
        """AnswerResult should be immutable."""
        result = AnswerResult(
            answer="test",
            sources=["src"],
            scores=[0.5],
        )
        with pytest.raises(AttributeError):
            result.answer = "new answer"


class TestRAGAgentInit:
    """Tests for RAGAgent.__init__."""

    def test_init_stores_retriever_and_llm(self):
        """RAGAgent.__init__ should store retriever and llm."""
        mock_retriever = MagicMock()
        mock_llm = MagicMock()
        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)
        assert agent.retriever is mock_retriever
        assert agent.llm is mock_llm


class TestRAGAgentAsk:
    """Tests for RAGAgent.ask method."""

    def test_ask_returns_string_answer(self):
        """RAGAgent.ask should return string answer."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            RetrievalResult(content="context", source="doc1", distance=0.1),
        ]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "This is the answer."

        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)
        result = agent.ask("What is test?")

        assert isinstance(result, str)
        assert result == "This is the answer."

    def test_ask_calls_retriever_and_llm(self):
        """RAGAgent.ask should call retriever and llm."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "Answer"

        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)
        agent.ask("Question")

        mock_retriever.retrieve.assert_called_once_with("Question")
        mock_llm.invoke.assert_called_once()


class TestRAGAgentAskWithSources:
    """Tests for RAGAgent.ask_with_sources method."""

    def test_ask_with_sources_returns_answer_result(self):
        """ask_with_sources should return AnswerResult."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            RetrievalResult(content="context", source="doc1", distance=0.1),
        ]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "Generated answer"

        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)
        result = agent.ask_with_sources("Question")

        assert isinstance(result, AnswerResult)
        assert result.answer == "Generated answer"
        assert result.sources == ["doc1"]
        assert result.scores == [0.1]
        assert result.metadata["retrieval_count"] == 1
        assert result.metadata["question"] == "Question"

    def test_ask_with_sources_handles_multiple_results(self):
        """ask_with_sources should correctly handle multiple retrieval results."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            RetrievalResult(content="context1", source="doc1", distance=0.1),
            RetrievalResult(content="context2", source="doc2", distance=0.2),
            RetrievalResult(content="context3", source="doc3", distance=0.3),
        ]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "Multi-source answer"

        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)
        result = agent.ask_with_sources("Complex question")

        assert result.sources == ["doc1", "doc2", "doc3"]
        assert result.scores == [0.1, 0.2, 0.3]
        assert result.metadata["retrieval_count"] == 3

    def test_ask_with_sources_empty_results(self):
        """ask_with_sources should handle empty retrieval results."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "No context answer"

        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)
        result = agent.ask_with_sources("Any question")

        assert result.answer == "No context answer"
        assert result.sources == []
        assert result.scores == []
        assert result.metadata["retrieval_count"] == 0


class TestRetrievalContextBuilding:
    """Tests for retrieval context construction."""

    def test_context_built_from_retrieval_results(self):
        """Context should be built from retrieval result contents."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            RetrievalResult(content="First context", source="doc1", distance=0.1),
            RetrievalResult(content="Second context", source="doc2", distance=0.2),
        ]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "Answer"

        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)
        agent.ask_with_sources("Question")

        # Verify LLM was called with prompt containing both contexts
        call_args = mock_llm.invoke.call_args[0][0]
        assert "First context" in call_args
        assert "Second context" in call_args

    def test_context_separated_by_double_newlines(self):
        """Context parts should be separated by double newlines."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            RetrievalResult(content="Context A", source="doc1", distance=0.1),
            RetrievalResult(content="Context B", source="doc2", distance=0.2),
        ]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "Answer"

        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)
        agent.ask_with_sources("Question")

        call_args = mock_llm.invoke.call_args[0][0]
        assert "Context A\n\nContext B" in call_args


class TestPromptConstruction:
    """Tests for prompt construction with context and question."""

    def test_prompt_contains_context_section(self):
        """Prompt should contain Context: section."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            RetrievalResult(content="Test context", source="doc1", distance=0.1),
        ]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "Answer"

        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)
        agent.ask_with_sources("Test question")

        call_args = mock_llm.invoke.call_args[0][0]
        assert "Context:" in call_args
        assert "Test context" in call_args

    def test_prompt_contains_question_section(self):
        """Prompt should contain Question: section."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            RetrievalResult(content="Some context", source="doc1", distance=0.1),
        ]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "Answer"

        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)
        agent.ask_with_sources("What is this?")

        call_args = mock_llm.invoke.call_args[0][0]
        assert "Question:" in call_args
        assert "What is this?" in call_args

    def test_prompt_contains_answer_section(self):
        """Prompt should contain Answer: section."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "Direct answer"

        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)
        agent.ask_with_sources("Simple question")

        call_args = mock_llm.invoke.call_args[0][0]
        assert "Answer:" in call_args

    def test_prompt_based_on_context_format(self):
        """Prompt should follow the expected format."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            RetrievalResult(content="CONTEXT_CONTENT", source="SRC1", distance=0.5),
        ]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "Result"

        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)
        agent.ask_with_sources("TEST_QUESTION")

        call_args = mock_llm.invoke.call_args[0][0]
        # Check format: Context: ... Question: ... Answer:
        assert "Context:" in call_args
        assert "CONTEXT_CONTENT" in call_args
        assert "Question:" in call_args
        assert "TEST_QUESTION" in call_args
        assert "Answer:" in call_args


class TestRAGAgentFormatSources:
    """Tests for RAGAgent.format_sources method."""

    def test_format_sources_includes_sources_label(self):
        """format_sources should include 'Sources:' label."""
        result = AnswerResult(
            answer="Answer",
            sources=["source1"],
            scores=[0.5],
        )
        mock_retriever = MagicMock()
        mock_llm = MagicMock()
        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)

        formatted = agent.format_sources(result)
        assert "Sources:" in formatted

    def test_format_sources_shows_all_sources(self):
        """format_sources should show all sources with indices."""
        result = AnswerResult(
            answer="Answer",
            sources=["source1", "source2", "source3"],
            scores=[0.9, 0.7, 0.5],
        )
        mock_retriever = MagicMock()
        mock_llm = MagicMock()
        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)

        formatted = agent.format_sources(result)
        assert "1. source1" in formatted
        assert "2. source2" in formatted
        assert "3. source3" in formatted

    def test_format_sources_includes_scores(self):
        """format_sources should include scores in output."""
        result = AnswerResult(
            answer="Answer",
            sources=["source1"],
            scores=[0.1234],
        )
        mock_retriever = MagicMock()
        mock_llm = MagicMock()
        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)

        formatted = agent.format_sources(result)
        assert "score: 0.1234" in formatted

    def test_format_sources_scores_to_4_decimals(self):
        """format_sources should show scores to 4 decimal places."""
        result = AnswerResult(
            answer="Answer",
            sources=["src1", "src2"],
            scores=[0.123456789, 0.987654321],
        )
        mock_retriever = MagicMock()
        mock_llm = MagicMock()
        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)

        formatted = agent.format_sources(result)
        assert "0.1235" in formatted  # rounded to 4 decimals
        assert "0.9877" in formatted  # rounded to 4 decimals

    def test_format_sources_empty_sources(self):
        """format_sources should handle empty sources list."""
        result = AnswerResult(
            answer="Answer",
            sources=[],
            scores=[],
        )
        mock_retriever = MagicMock()
        mock_llm = MagicMock()
        agent = RAGAgent(retriever=mock_retriever, llm=mock_llm)

        formatted = agent.format_sources(result)
        assert "Sources:" in formatted
        assert "1." not in formatted  # no numbered items