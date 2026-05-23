import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*generation_config.*", category=FutureWarning)

from deepeval.metrics import (
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    AnswerRelevancyMetric, 
    FaithfulnessMetric,
)
from deepeval.test_case import LLMTestCase
from deepeval.models import GPTModel
from deepeval import evaluate
import json

if __name__=="__main__":
    llm=GPTModel(model="qwen3.5-4b@q8_0",base_url="http://127.0.0.1:1234/v1",api_key="none",temperature=0.2)

    with open("eval_results/.dataset.json",'r',encoding="utf-8") as f:
        dataset=json.load(f)
    test_cases:list[LLMTestCase]=[]
    for tc in dataset[:40]:
        test_cases.append(
            LLMTestCase(
                input=tc["input"],
                actual_output=tc["actual_output"],
                expected_output=tc["expected_output"],
                retrieval_context=tc["retrieval_context"]
            )
        )
    #初始化评估指标
    contextual_precision = ContextualPrecisionMetric(model=llm,async_mode=True,include_reason=False)
    contextual_recall = ContextualRecallMetric(model=llm,async_mode=True,include_reason=False)
    #contextual_relevancy = ContextualRelevancyMetric(model=llm)
    answer_relevancy = AnswerRelevancyMetric(model=llm,async_mode=True,include_reason=False)
    #faithfulness = FaithfulnessMetric(model=llm,async_mode=False)
    #执行评估
    evaluate(test_cases=test_cases,metrics=[contextual_precision, contextual_recall, answer_relevancy])