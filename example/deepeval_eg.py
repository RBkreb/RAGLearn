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
#from deepeval import evaluate
from deepeval.models import GPTModel



if __name__=="__main__":
    llm=GPTModel(model="qwen3.5-4b",base_url="http://127.0.0.1:1234/v1",api_key="none")
    #生成回答测试
    #print(llm.generate("document:"Her first acting role of 2006 was in the comedy film The Pink Panther starring opposite Steve Martin, grossing $158.8 million at the box office worldwide. Her second film Dreamgirls, the film version of the 1981 Broadway musical loosely based on The Supremes, received acclaim from critics and grossed $154 million internationally. In it, she starred opposite Jennifer Hudson, Jamie Foxx, and Eddie Murphy playing a pop singer based on Diana Ross. To promote the film, Beyoncé released \"Listen\" as the lead single from the soundtrack album. In April 2007, Beyoncé embarked on The Beyoncé Experience, her first worldwide concert tour, visiting 97 venues and grossed over $24 million.[note 1] Beyoncé conducted pre-concert food donation drives during six major stops in conjunction with her pastor at St. John's and America's Second Harvest. At the same time, B'Day was re-released with five additional songs, including her duet with Shakira \"Beautiful Liar\"query:For what movie did Beyonce receive  her first Golden Globe nomination?"))
    
    #单例
    test_case = LLMTestCase(
    input="I'm on an F-1 visa, how long can I stay in the US after graduation?",
    actual_output="You can stay up to 30 days after completing your degree.",
    expected_output="You can stay up to 60 days after completing your degree.",
    retrieval_context=[
        "If you are in the U.S. on an F-1 visa, you are allowed to stay for 60 days after completingyour degree, unless you have applied for and been approved to participate in OPT."
    ]
    )
    #初始化评估指标
    #contextual_precision = ContextualPrecisionMetric(model=llm)
    #contextual_recall = ContextualRecallMetric(model=llm)
    #contextual_relevancy = ContextualRelevancyMetric(model=llm)
    #answer_relevancy = AnswerRelevancyMetric(model=llm)
    faithfulness = FaithfulnessMetric(model=llm,async_mode=False)
    #执行评估
    #answer_relevancy.measure(test_case)
    #print("Score: ", answer_relevancy.score)
    #print("Reason: ", answer_relevancy.reason)
    faithfulness.measure(test_case)
    print("Score: ", faithfulness.score)
    print("Reason: ", faithfulness.reason)

    #多例
    #evaluate(test_cases=[test_cases],metrics=[contextual_precision, contextual_recall, contextual_relevancy])
