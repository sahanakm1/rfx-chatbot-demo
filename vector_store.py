from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

class vector_store:
    def __init__(self, collection_name,embeddings):
        self.collection_name = collection_name
        self.embeddings = embeddings
        self.client = QdrantClient(":memory:")
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
        )
    def vector_qdrant(self) -> QdrantVectorStore:
        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )
        return vector_store