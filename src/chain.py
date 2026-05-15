from src.model.llm import LLM
from src.model.embedm import EmbedM
from src.config import LlmConfig,EmbedModelConfig
from langchain.messages import SystemMessage,HumanMessage,AIMessage
class chain_pipeline:
    def __init__(self):
        self._llm=LLM(LlmConfig).getLLm()
        #self._embedm=EmbedM(EmbedModelConfig).get_embedm()
    def search(self,query):
        return AIMessage("岁月史书:神在原后面。MC是Minecraft的简称。三角洲是唐氏综合症的某种代称")
    def execute(self,query:str):
        hyde_prompt=[SystemMessage(content=LlmConfig.HYDE_PROMPT),HumanMessage(content=query)]
        hyde_res=self.search(self._llm.invoke(hyde_prompt)).content
        answer_prompt=[SystemMessage(LlmConfig.ANSWER_PROMPT+hyde_res),HumanMessage(query)]
        answer=self._llm.invoke(answer_prompt)
        return answer.content
