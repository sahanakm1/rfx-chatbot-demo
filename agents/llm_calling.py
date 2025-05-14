from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from agents.azure_openai_config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_BASE_URL,
    AZURE_OPENAI_API_VERSION,
    GPT_DEPLOYMENT_NAME,
    EMBEDDING_DEPLOYMENT_NAME,
)

class llm_calling:
    def __init__(self):
        pass  # All config is loaded from the shared module

    def call_llm(self):
        return AzureChatOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_BASE_URL,
            deployment_name=GPT_DEPLOYMENT_NAME,
            temperature=0,
        )

    def call_embed_model(self):
        return AzureOpenAIEmbeddings(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_BASE_URL,
            deployment=EMBEDDING_DEPLOYMENT_NAME,
        )

# from langchain_ollama import ChatOllama
# from langchain_huggingface import HuggingFaceEmbeddings

# # Helper class to initialize both LLMs and embedding models
# class llm_calling:
#     def __init__(self, model_name="mistral", embedding_model="all-MiniLM-L6-v2"):
#         self.model_name = model_name
#         self.embedding_model = embedding_model

#     # Instantiate and return a language model (ChatOllama)
#     def call_llm(self):
#         try:
#             return ChatOllama(model=self.model_name, temperature=0)
#         except Exception as e:
#             raise RuntimeError(f"Failed to load LLM '{self.model_name}': {e}")

#     # Instantiate and return an embedding model (HuggingFace)
#     def call_embed_model(self):
#         embedding_model = HuggingFaceEmbeddings(model_name=self.embedding_model)
#         return embedding_model