from langchain_ollama import ChatOllama, OllamaLLM
from langchain_huggingface import HuggingFaceEmbeddings


class llm_calling:
    def __init__(self, model_name="mistral",embedding_model="sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embedding_model = embedding_model

    def call_llm(self):
        model =  ChatOllama(model=self.model_name,temperature=0)
        return model
    
    def call_embed_model(self):
        embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        return embedding_model