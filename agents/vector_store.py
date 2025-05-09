from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, SparseVectorParams

class vector_store:
    def __init__(self, collection_name, embeddings, path):
        self.collection_name = collection_name
        self.embeddings = embeddings
        self.path = path

    def vector_qdrant_dense(self, create_if_not_exists=True, force_recreate=False) -> QdrantVectorStore:
        client = QdrantClient(path=self.path)

        if force_recreate:
            try:
                print(f"[INFO] Forcing recreation of collection: {self.collection_name}")
                client.delete_collection(self.collection_name)
            except Exception as e:
                print(f"[WARNING] Failed to delete collection: {e}")

        if create_if_not_exists and not client.collection_exists(collection_name=self.collection_name):
            print(f"[INFO] Creating new collection: {self.collection_name} with vector size 4096")
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=4096, distance=Distance.COSINE)
            )

        print(f"[INFO] Connecting to Qdrant collection: {self.collection_name}")
        return QdrantVectorStore(
            client=client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
            retrieval_mode=RetrievalMode.DENSE,
        )

    def vector_qdrant_sparse(self) -> QdrantVectorStore:
        sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
        client = QdrantClient(path=self.path)
        client.create_collection(
            collection_name=self.collection_name,
            vectors_config={"dense": VectorParams(size=3072, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams(index=models.SparseIndexParams(on_disk=False))}
        )
        return QdrantVectorStore(
            client=client,
            collection_name=self.collection_name,
            sparse_embedding=sparse_embeddings,
            retrieval_mode=RetrievalMode.SPARSE,
            sparse_vector_name="sparse",
        )

    def vector_qdrant_hybrid(self) -> QdrantVectorStore:
        sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
        client = QdrantClient(path=self.path)
        client.create_collection(
            collection_name=self.collection_name,
            vectors_config={"dense": VectorParams(size=3072, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams(index=models.SparseIndexParams(on_disk=False))}
        )
        return QdrantVectorStore(
            client=client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
            sparse_embedding=sparse_embeddings,
            retrieval_mode=RetrievalMode.HYBRID,
            vector_name="dense",
            sparse_vector_name="sparse",
        )
    

from functools import lru_cache
from agents.llm_calling import llm_calling

@lru_cache(maxsize=1)
def get_cached_vector_store(collection_name="rfx_classification", path="./qdrant_store"):
    print("[INFO] Using cached Qdrant vector store")
    llm = llm_calling(model_name="mistral")  # Or make this dynamic if needed
    embed_model = llm.call_embed_model()

    store = vector_store(collection_name=collection_name, embeddings=embed_model, path=path)
    return store.vector_qdrant_dense(create_if_not_exists=False, force_recreate=False)
