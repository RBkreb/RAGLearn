"""Unit tests for the CrossEncoder reranker and its score normalization.

These tests exercise the reranking logic in ``src.chain`` without loading the
real Qwen3-Reranker weights: a tiny fake model stands in for the HuggingFace
cross-encoder and returns the raw log-odds scores the real model produces.
"""

import pytest
from langchain_core.documents import Document

from src.chain import CEReranker, normalize_score
from langchain_community.cross_encoders.base import BaseCrossEncoder


class FakeCrossEncoder(BaseCrossEncoder):
    """Returns pre-seeded raw scores in call order (log-odds style)."""

    def __init__(self, scores: list[float]) -> None:
        self._scores = scores

    def score(self, text_pairs: list[tuple[str, str]]) -> list[float]:
        return self._scores[: len(text_pairs)]


def _docs(n: int) -> list[Document]:
    return [Document(page_content=f"doc-{i}") for i in range(n)]


class TestNormalizeScore:
    """normalize_score maps unbounded log-odds into the 0-1 threshold space."""

    def test_zero_maps_to_half(self) -> None:
        assert normalize_score(0.0) == pytest.approx(0.5)

    def test_positive_maps_above_half(self) -> None:
        assert normalize_score(4.438) == pytest.approx(0.9883, abs=1e-3)

    def test_negative_maps_below_half(self) -> None:
        assert normalize_score(-11.4) == pytest.approx(1.1e-5, abs=1e-6)

    def test_monotonic(self) -> None:
        assert normalize_score(-10) < normalize_score(0) < normalize_score(10)

    def test_extremes_do_not_overflow(self) -> None:
        # Without clamping, exp(1e9) raises OverflowError.
        assert normalize_score(1e9) == pytest.approx(1.0)
        assert 0.0 <= normalize_score(-1e9) < 1e-20

    def test_output_stays_in_unit_interval(self) -> None:
        for raw in (-1e9, -50, -5, 0, 5, 50, 1e9):
            assert 0.0 <= normalize_score(raw) <= 1.0


class TestCEReranker:
    """CEReranker.compress_documents normalization, ordering and truncation."""

    def test_scores_are_normalized(self) -> None:
        reranker = CEReranker(model=FakeCrossEncoder([4.0, -8.0]), top_n=2)
        out = reranker.compress_documents(_docs(2), "q")
        scores = [s for _, s in out]
        assert all(0.0 <= s <= 1.0 for s in scores)

    def test_results_sorted_by_score_desc(self) -> None:
        # Third doc gets the highest score; output must be reordered.
        reranker = CEReranker(model=FakeCrossEncoder([-5.0, 1.0, 6.0]), top_n=3)
        out = reranker.compress_documents(_docs(3), "q")
        assert [d.page_content for d, _ in out] == ["doc-2", "doc-1", "doc-0"]
        assert out[0][1] > out[1][1] > out[2][1]

    def test_respects_top_n(self) -> None:
        # Regression: the override used to ignore top_n and return every candidate.
        reranker = CEReranker(model=FakeCrossEncoder(list(range(10))), top_n=3)
        out = reranker.compress_documents(_docs(10), "q")
        assert len(out) == 3

    def test_top_n_larger_than_input(self) -> None:
        reranker = CEReranker(model=FakeCrossEncoder([1.0, 2.0]), top_n=99)
        out = reranker.compress_documents(_docs(2), "q")
        assert len(out) == 2

    def test_empty_documents_returns_empty(self) -> None:
        # Must not call the model at all with no documents.
        reranker = CEReranker(model=FakeCrossEncoder([]), top_n=3)
        assert reranker.compress_documents([], "q") == []

    def test_returns_document_score_pairs(self) -> None:
        reranker = CEReranker(model=FakeCrossEncoder([1.0, 2.0]), top_n=2)
        out = reranker.compress_documents(_docs(2), "q")
        assert all(isinstance(d, Document) and isinstance(s, float) for d, s in out)
