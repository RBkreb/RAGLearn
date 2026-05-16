from langchain_chroma import Chroma
from src.config import IndexConfig
from src.model.embedm import EmbedM
from src.chunker import LineSplitter
from src.utils.bm25 import BM25Retriever
class Pipeline:
	def __init__(self):
		self.config=IndexConfig()
		self._emb=EmbedM().get()
		self._vector_store=Chroma(
			collection_name="collection",
			persist_directory=self.config.persist_directory,
			embedding_function=self._emb
		)
		self._splitter=LineSplitter()
		self._BM25=BM25Retriever()

	def execute(self,file_path: str):
		Docs=self._splitter.split_file(file_path)
		self._vector_store.add_documents(documents=Docs)
		self._BM25.index_from_chroma(self._vector_store)
		self._BM25.save(self.config.persist_directory+"/BM25")

	def get_vs(self):
		return self._vector_store
	
	def get_BM25(self):
		return self._BM25
	