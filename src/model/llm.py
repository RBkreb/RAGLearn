from langchain_openai import ChatOpenAI
from src.config import LlmConfig
class LLM:
    def __init__(self,config:LlmConfig=None):
        if config:
            self.config=config
        else:
            self.config=LlmConfig()
        print(self.config.model_name)
        self._llm=ChatOpenAI(
            model=self.config.model_name,
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            temperature=self.config.temperature
        )
    def get(self):
        return self._llm