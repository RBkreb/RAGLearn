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
from deepeval.evaluate import AsyncConfig
import json

async_config=AsyncConfig(
    run_async=True,
    throttle_value=0,
    max_concurrent=4
)

if __name__=="__main__":
    llm=GPTModel(model="compassjudger-7b-it",base_url="http://127.0.0.1:1234/v1",api_key="none")

    def _clean(s: str) -> str:
        return s.replace('"', '')

    with open("eval_results/.dataset.json",'r',encoding="utf-8") as f:
        dataset=json.load(f)
    test_cases:list[LLMTestCase]=[]
    for tc in dataset:
        test_cases.append(
            LLMTestCase(
                input=_clean(tc["input"]),
                actual_output=_clean(tc["actual_output"]),
                expected_output=_clean(tc["expected_output"]),
                retrieval_context=[_clean(ctx) for ctx in tc["retrieval_context"]]
            )
        )
    #初始化评估指标
    contextual_precision = ContextualPrecisionMetric(model=llm,async_mode=True,include_reason=False)
    contextual_recall = ContextualRecallMetric(model=llm,async_mode=True,include_reason=False)
    #contextual_relevancy = ContextualRelevancyMetric(model=llm)
    answer_relevancy = AnswerRelevancyMetric(model=llm,async_mode=True,include_reason=False)
    #faithfulness = FaithfulnessMetric(model=llm,async_mode=False)
    #执行评估
    '''ct=0
    res=[]
    CT_P=0
    CT_R=0
    AS_R=0
    while ct<len(test_cases):
        try:
            tc=test_cases[ct]
            contextual_precision.measure(tc)
            contextual_recall.measure(tc)
            answer_relevancy.measure(tc)
            print("CT_P:"+str(contextual_precision.score)+"  CT_R:"+str(contextual_recall.score)+"  R:"+str(answer_relevancy.score))
            CT_P+=contextual_precision.score
            CT_R+=contextual_recall.score
            AS_R+=answer_relevancy.score
            res.append({"CT_P":contextual_precision.score,"CT_R":contextual_recall.score,"AS_R":answer_relevancy.score})
        except DeepEvalError:
            print("retry:"+str(ct))
            ct-=1
        ct+=1
        
    with open("eval_results/res.json",'w',encoding="utf-8") as f:
        json.dump(res,f,ensure_ascii=False,indent=2)

    print("Total:"+str(len(test_cases)))
    print("Average CT_P:"+str(CT_P/len(test_cases)))
    print("Average CT_R:"+str(CT_R/len(test_cases)))
    print("Average AS_R:"+str(AS_R/len(test_cases)))'''
    evaluate(test_cases=test_cases,metrics=[contextual_precision, contextual_recall, answer_relevancy],async_config=async_config)