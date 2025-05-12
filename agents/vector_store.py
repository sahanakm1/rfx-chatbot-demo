# agents/vector_store.py

from langchain_qdrant import QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain.embeddings.base import Embeddings

class vector_store:
    def __init__(self, collection_name: str, embeddings: Embeddings, path: str = "./qdrant_store"):
        self.collection_name = collection_name
        self.embeddings = embeddings
        self.path = path

    def vector_qdrant_dense(self, create_if_not_exists=True, force_recreate=True) -> QdrantVectorStore:
        client = QdrantClient(path=self.path)

        if force_recreate:
            try:
                print(f"[INFO] Forzando recreación de la colección: {self.collection_name}")
                client.delete_collection(self.collection_name)
            except Exception as e:
                print(f"[WARNING] No se pudo borrar la colección: {e}")

        if create_if_not_exists and not client.collection_exists(collection_name=self.collection_name):
            print(f"[INFO] Creando nueva colección: {self.collection_name} con tamaño 4096")
            sample_vector = self.embeddings.embed_documents(["dummy"])[0]
            dimension = len(sample_vector)

            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
            )

        print(f"[INFO] Conectado a colección Qdrant: {self.collection_name}")
        return QdrantVectorStore(
            client=client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
            retrieval_mode=RetrievalMode.DENSE,
        )


def get_cached_vector_store(collection_name: str, embeddings: Embeddings, path: str = "./qdrant_store", ensure_exists: bool = False, force_recreate: bool = False) -> QdrantVectorStore:
    print(f"[INFO] Usando Qdrant cache para colección: {collection_name}")
    store = vector_store(collection_name=collection_name, embeddings=embeddings, path=path)
    return store.vector_qdrant_dense(create_if_not_exists=ensure_exists, force_recreate=force_recreate)