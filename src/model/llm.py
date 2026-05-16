from langchain_openai import ChatOpenAI
from src.config import LlmConfig
class LLM:
    def __init__(self):

        self.config=LlmConfig()
        self._llm=ChatOpenAI(
            name=self.config.model_name,
            base_url=self.config.base_url,
            api_key=self.config.api_key
        )
    def get(self):
        return self._llm