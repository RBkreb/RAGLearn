from src.model.llm import LLM
from src.pipeline.pipe import Pipeline
from src.config import LlmConfig,IndexConfig
from src.utils.hash import compute_hash
from langchain.messages import SystemMessage,HumanMessage,AIMessage
from langchain.agents import create_agent,AgentState
from pydantic import BaseModel,Field
from langchain_core.documents import Document

class schemaF(BaseModel):
    keywords:list[str]=Field(description="keywords list")
    documents:str=Field(description="hypothetical document")
    #answer:str=Field(description="answer")
class chain_pipeline:
    def __init__(self):
        self._llm=LLM().get()
        self._pipline=Pipeline()
        self._vs=self._pipline.get_vs()
        self._bm25=self._pipline.get_BM25().load(IndexConfig.persist_directory+"/BM25")
        self._HyDE_agent=create_agent(
            self._llm,
            response_format=schemaF
        )
        self._agent=create_agent(
            self._llm
        )
    def _rerank(self, bm25_results: list[tuple[str, float]], hyde_results: list[tuple[Document, float]], k: int = 3) -> list[Document]:
        """RFF reranking: combine BM25 and vector scores into a final ranking."""
        if not bm25_results and not hyde_results:
            return []

        all_scores: dict[str, tuple[float, float]] = {}  # doc_content -> (bm25_score, vector_score)

        for content, bm25_score in bm25_results:
            if content not in all_scores:
                all_scores[content] = (bm25_score, 0.0)
            else:
                existing = all_scores[content]
                all_scores[content] = (existing[0] + bm25_score, existing[1])

        for doc, vector_score in hyde_results:
            content = doc.page_content
            # vector_score is distance (lower=better), convert to similarity
            sim_score = 1.0 / (1.0 + vector_score)
            if content not in all_scores:
                all_scores[content] = (0.0, sim_score)
            else:
                existing = all_scores[content]
                all_scores[content] = (existing[0], existing[1] + sim_score)

        # RFF: sum normalized scores
        reranked = sorted(all_scores.items(), key=lambda x: x[1][0] + x[1][1], reverse=True)
        return [Document(page_content=content) for content, _ in reranked[:k]]

    def search(self, keywords: list[str], HyDEdocuments: str):
        """Search documents using BM25 + Chroma hybrid retrieval."""
        # 1. BM25 multi-keyword aggregation, keep highest score
        all_docs: dict[str, float] = {}
        for keyword in keywords:
            docs, scores = self._bm25.retrieve(keyword, k=10)
            for doc, score in zip(docs, scores):
                if doc not in all_docs or all_docs[doc] < score:
                    all_docs[doc] = score

        # 2. Hash lookup + Chroma retrieval
        bm25_res: list[tuple[str, float]] = []  # (doc_content, bm25_score)
        for doc, bm25_score in all_docs.items():
            h = compute_hash(doc)
            chroma_result = self._vs.get(
                where={"hash": h}, include=["documents", "metadatas"]
            )
            if chroma_result["documents"]:
                doc_content = chroma_result["documents"][0]
                bm25_res.append((doc_content, bm25_score))

        # 3. HyDE vector search
        hyde_res: list[tuple[Document, float]] = self._vs.similarity_search_with_score(HyDEdocuments, k=10)

        # 4. RFF reranking
        final_docs = self._rerank(bm25_res, hyde_res, k=3)
        context = "context:\n".join([doc.page_content for doc in final_docs])
        return context
    def execute(self,query:str):

        hyde_prompt=AgentState(messages=[SystemMessage(content=LlmConfig.HYDE_PROMPT),HumanMessage(content=query)])

        hyde_res:schemaF=self._HyDE_agent.invoke(hyde_prompt)["structured_response"]
        search_res=self.search(hyde_res.keywords,hyde_res.documents)
        answer_prompt=AgentState(messages=[SystemMessage(LlmConfig.ANSWER_PROMPT+search_res),HumanMessage(query)])

        answer:AIMessage=self._agent.invoke(answer_prompt)["messages"][-1]

        return answer.content
