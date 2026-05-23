from src.model.llm import LLM
from src.pipeline.pipe import Pipeline
from src.config import LlmConfig,IndexConfig
from src.utils.hash import compute_hash
from langchain.messages import SystemMessage,HumanMessage,AIMessage
from langchain.agents import create_agent,AgentState
from pydantic import BaseModel,Field
from langchain_core.documents import Document
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from dataclasses import dataclass
@dataclass
class schemaF(BaseModel):
    keywords:list[str]=Field(description="keywords list")
    documents:str=Field(description="hypothetical document")
@dataclass
class answerF(BaseModel):
    answer:str=Field(description="answer")
    availabe:bool=Field(description="mark of answered")
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
            self._llm,
            response_format=answerF
        )
        
        self._crossencoder=HuggingFaceCrossEncoder(model_name="Qwen/Qwen3-Reranker-0.6B",model_kwargs={"device": "cpu","local_files_only":True})
        self._cereranker=CrossEncoderReranker(model=self._crossencoder,top_n=3)
    def _rerank(self, bm25_results: list[tuple[str, float]], hyde_results: list[tuple[Document, float]], k: int = 3,RRF_K:int=60,weight_Embed:float=0.4) -> list[Document]:
        """RRF reranking: combine BM25 and vector results using Reciprocal Rank Fusion.

        Uses true RRF formula: RRF(d) = Σ 1/(K + rank_i(d))
        where K=60 and rank starts at 1. This normalizes across retrieval methods
        so that top-ranked documents in either method contribute equally,
        regardless of raw score magnitude differences.
        """
        if not bm25_results and not hyde_results:
            return []
        weight_bm25=1-weight_Embed
        rrf_scores: dict[str, float] = {}

        # BM25 ranks (sorted by score desc already)
        for rank, (content, _) in enumerate(bm25_results):
            rrf = weight_bm25 * 1.0 / (RRF_K + rank + 1) 
            rrf_scores[content] = rrf_scores.get(content, 0.0) + rrf

        # Vector ranks (sorted by distance asc already)
        for rank, (doc, _) in enumerate(hyde_results):
            content = doc.page_content
            rrf = weight_Embed * 1.0 / (RRF_K + rank + 1)
            rrf_scores[content] = rrf_scores.get(content, 0.0) + rrf

        reranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [Document(page_content=content) for content, _ in reranked[:k]]

    def search(self, keywords: list[str], HyDEdocuments: str,query:str,k:int=3):
        """Search documents using BM25 + Chroma hybrid retrieval."""
        # 1. BM25 multi-keyword aggregation, keep highest score
        all_docs: dict[str, float] = {}
        for keyword in keywords:
            docs, scores = self._bm25.retrieve(keyword, k=(10+k)//len(keywords))
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
        hyde_res: list[tuple[Document, float]] = self._vs.similarity_search_with_score(HyDEdocuments, k=10+k)

        # 4. RRF reranking
        RRF_docs = self._rerank(bm25_res, hyde_res, k=7+k)
        # 5. CrossEncoder reranking
        self._cereranker.top_n=k
        final_docs=self._cereranker.compress_documents(RRF_docs,query)
        context = "context:\n".join([doc.page_content for doc in final_docs])
        return context
    def execute(self,query:str,k:int=3,max_retry:int=3):
        search_res = ""
        import time as _time
        for attempt in range(max_retry):
            try:
                hyde_prompt=AgentState(messages=[SystemMessage(content=LlmConfig.HYDE_PROMPT),HumanMessage(content=query)])
                self._llm.temperature=0.8
                hyde_res:schemaF=self._HyDE_agent.invoke(hyde_prompt)["structured_response"]
                #print(hyde_res.keywords)
                search_res=self.search(hyde_res.keywords,hyde_res.documents,query,k=k+attempt)
                answer_prompt=AgentState(messages=[SystemMessage(LlmConfig.ANSWER_PROMPT+search_res),HumanMessage(query)])
                self._llm.temperature=0.1
                answer:answerF=self._agent.invoke(answer_prompt)["structured_response"]
                if answer.availabe:
                    break
            except Exception as e:
                err = str(e)
                if "crashed" in err or "No models loaded" in err or "400" in err:
                    wait = 5 * (attempt + 1)
                    print(f"  [LLM crash, retry in {wait}s]")
                    _time.sleep(wait)
                    continue
                raise

        # Extract contexts from search response
        contexts = [c.strip() for c in search_res.split("context:\n") if c.strip()]
        return answer, contexts
