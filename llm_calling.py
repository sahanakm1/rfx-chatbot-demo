from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings

class llm_calling:
    def __init__(self, model_name="llama3.2:latest",embedding_model="llama3.2:latest"):
        self.model_name = model_name
        self.embedding_model = embedding_model

    def call_llm(self):
        model = llm = ChatOllama(model=self.model_name,temperature=0
                                 ,# other params...
                                 )
        return model
    
    def call_embed_model(self):
        embedding_model = OllamaEmbeddings(model=self.embedding_model)
        return embedding_model


