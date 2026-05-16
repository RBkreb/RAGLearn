from src.config import EmbedModelConfig
from langchain_openai import OpenAIEmbeddings

class EmbedM:
    def __init__(self):
        self.config=EmbedModelConfig()
        self._embedm=OpenAIEmbeddings(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            model=self.config.model_name,
            dimensions=self.config.dimensions,
            embedding_ctx_length=self.config.n_ctx,
            check_embedding_ctx_length=False
        )
    def get(self) -> OpenAIEmbeddings:
        return self._embedm
    
    def _sanitize_text(self, text: str) -> str:
        return text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

    def embed(self, text: str) -> list[float]:
        try:
            clean_text = self._sanitize_text(text)
            return self._embedm.embed_query(clean_text)
        except Exception as e:
            raise ValueError(f"Embedding generation failed: {e}") from e

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        try:
            clean_texts = [self._sanitize_text(t) for t in texts]
            return self._embedm.embed_documents(clean_texts) 
        except Exception as e:
            raise ValueError(f"Batch embedding generation failed: {e}") from e