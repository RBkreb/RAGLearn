from src.model.llm import LLM
from src.pipeline.pipe import Pipeline
from src.config import LlmConfig,IndexConfig
from langchain.messages import SystemMessage,HumanMessage,AIMessage
from langchain.agents import create_agent,AgentState
from pydantic import BaseModel,Field


class schemaF(BaseModel):
    keywords:list[str]=Field(description="keywords list")
    documents:str=Field(description="hypothetical document")
    #answer:str=Field(description="answer")
class chain_pipeline:
    def __init__(self):
        self._llm=LLM().get()
        self._pipline=Pipeline()
        self._vs=self._pipline.get_vs()
        self._bm25=self._pipline.get_BM25()
        self._bm25.load(IndexConfig.persist_directory+"/BM25")
        self._HyDE_agent=create_agent(
            self._llm,
            response_format=schemaF
        )
        self._agent=create_agent(
            self._llm
        )
    def search(self,keywords:list[str],documents:str):
        bm25_res=[]
        for keyword in keywords:
            bm25_res.append(self._bm25.retrieve(keyword,k=10))
        
        return AIMessage("")
    def execute(self,query:str):

        hyde_prompt=AgentState(messages=[SystemMessage(content=LlmConfig.HYDE_PROMPT),HumanMessage(content=query)])

        hyde_res:schemaF=self._HyDE_agent.invoke(hyde_prompt)["structured_response"]
        search_res=self.search(hyde_res.keywords,hyde_res.documents).content

        answer_prompt=[SystemMessage(LlmConfig.ANSWER_PROMPT+hyde_res),HumanMessage(query)]

        answer=self._llm.invoke(answer_prompt)

        return answer.content
