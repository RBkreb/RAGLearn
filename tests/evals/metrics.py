"""Shared metrics for RAG single-turn eval using local LM Studio via GPTModel."""
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*generation_config.*", category=FutureWarning)

from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRelevancyMetric,
)
from deepeval.models import GPTModel

_eval_model = GPTModel(
    model="qwen3.5-4b",
    api_key="none",
    base_url="http://127.0.0.1:1234/v1",
)

SINGLE_TURN_NO_TRACING_METRICS = [
    AnswerRelevancyMetric(threshold=0.5, model=_eval_model, async_mode=False),
    FaithfulnessMetric(threshold=0.5, model=_eval_model, async_mode=False),
    ContextualRelevancyMetric(threshold=0.5, model=_eval_model, async_mode=False),
]
