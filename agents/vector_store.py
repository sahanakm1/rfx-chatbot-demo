# agents/vector_store.py

from langchain_qdrant import QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain.embeddings.base import Embeddings
from functools import lru_cache

@lru_cache(maxsize=1)
def get_qdrant_local_client(path: str = "./qdrant_store"):
    from qdrant_client import QdrantClient
    return QdrantClient(path=path)

# Class to encapsulate vector store logic
class vector_store:
    def __init__(self, collection_name: str, embeddings: Embeddings, path: str = "./qdrant_store"):
        self.collection_name = collection_name
        self.embeddings = embeddings
        self.path = path

    # Create or retrieve a Qdrant vector store with dense embeddings
    def vector_qdrant_dense(self, create_if_not_exists=True, force_recreate=True) -> QdrantVectorStore:
        from .vector_store import get_qdrant_local_client
        client = get_qdrant_local_client(path=self.path)

        # Force recreate the collection (for clean rebuilds)
        if force_recreate:
            try:
                print(f"[INFO] Forcing collection recreation: {self.collection_name}")
                client.delete_collection(self.collection_name)
            except Exception as e:
                print(f"[WARNING] Could not delete collection: {e}")

        # Create collection if it doesn't exist
        if create_if_not_exists and not client.collection_exists(collection_name=self.collection_name):
            print(f"[INFO] Creating new collection: {self.collection_name} with dimension 4096")
            sample_vector = self.embeddings.embed_documents(["dummy"])[0]
            dimension = len(sample_vector)

            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
            )

        print(f"[INFO] Connected to Qdrant collection: {self.collection_name}")
        return QdrantVectorStore(
            client=client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
            retrieval_mode=RetrievalMode.DENSE,
        )

# Helper function to reuse or create a cached Qdrant vector store
def get_cached_vector_store(
    collection_name: str, 
    embeddings: Embeddings, 
    path: str = "./qdrant_store", 
    ensure_exists: bool = False, 
    force_recreate: bool = False
) -> QdrantVectorStore:
    print(f"[INFO] Using Qdrant cache for collection: {collection_name}")
    store = vector_store(collection_name=collection_name, embeddings=embeddings, path=path)
    return store.vector_qdrant_dense(create_if_not_exists=ensure_exists, force_recreate=force_recreate)
