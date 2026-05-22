from dataclasses import dataclass

@dataclass
class EmbedModelConfig:
    """Configuration for embedding models."""
    model_name:str="text-embedding-nomic-embed-text-v1.5"
    base_url:str="http://127.0.0.1:1234/v1"
    api_key:str="nokey"
    n_ctx: int = 1024
    dimensions:int =1024
    max_tokens: int = 512
    timeout: int = 120


@dataclass
class IndexConfig:
    """Configuration for document indexing."""

    chunk_size: int = 600
    chunk_overlap: int = 60
    persist_directory: str = "./chroma_db"

@dataclass
class LlmConfig:
    model_name:str="qwen3.5-4b"
    base_url:str="http://127.0.0.1:1234/v1"
    api_key:str="nokey"

    DEFAULT_PROMPT="You are a helpful assistant"

    ANSWER_PROMPT='''You are a strict retrieval-augmented assistant. Your only source of truth is the retrieved context below.
Rules:
1. Answer solely based on the retrieved context. Do not use any external knowledge.
2. If the context contains sufficient information, answer concisely (1-3 sentences) and set mark of answered to True.
3. If the context is insufficient or irrelevant, leave answer blank and set mark of answered to False.
4. Never speculate, guess, or fabricate.
5. If the context is about a different person/place/event than what was asked, treat it as insufficient.'''

    HYDE_PROMPT='''You are a HyDE generator. Given a question, produce keywords and a hypothetical Wikipedia paragraph that would answer it. The paragraph is used for semantic search — it does NOT need to be factually true, but MUST be rich in descriptive vocabulary and concrete details.

=== STEP 1: keywords === (field: "keywords")
Extract named entities and key terms, ordered by importance:
  - Proper nouns: person names, place names, organization names, event names, work titles
  - Numbers, dates, quantities from the query
  - Core topic words + 1-2 synonyms/variants (e.g. "Beyoncé" / "Beyonce")

=== STEP 2: hypothetical paragraph === (field: "documents")
Write 2-3 sentences DESCRIBING THE EVENT that answers the question, as if from Wikipedia.
You MUST include: full names of entities, a complete sentence about what happened (who, what, when, where), and domain-specific vocabulary.
CRITICAL: Do NOT output just a date, number, or single word. Write a COMPLETE DESCRIPTIVE PARAGRAPH.'''
