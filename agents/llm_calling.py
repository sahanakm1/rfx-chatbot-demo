from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings

# Helper class to initialize both LLMs and embedding models
class llm_calling:
    def __init__(self, model_name="mistral", embedding_model="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embedding_model = embedding_model

    # Instantiate and return a language model (ChatOllama)
    def call_llm(self):
        try:
            return ChatOllama(model=self.model_name, temperature=0)
        except Exception as e:
            raise RuntimeError(f"Failed to load LLM '{self.model_name}': {e}")

    # Instantiate and return an embedding model (HuggingFace)
    def call_embed_model(self):
        embedding_model = HuggingFaceEmbeddings(model_name=self.embedding_model)
        return embedding_model