from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, SparseVectorParams

class vector_store:
    def __init__(self, collection_name,embeddings,path):
        self.collection_name = collection_name
        self.embeddings = embeddings
        self.path = path
        
    def vector_qdrant_dense(self) -> QdrantVectorStore:
        #client = QdrantClient(path="./tmp/langchain_qdrant")
        client = QdrantClient(path=self.path)
        client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
        )
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
            retrieval_mode=RetrievalMode.DENSE,
        )
        return vector_store
    
    def vector_qdrant_sparse(self) -> QdrantVectorStore:
        sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
        client = QdrantClient(path=self.path)
        client.create_collection(
            collection_name=self.collection_name,
            vectors_config={"dense": VectorParams(size=3072, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams(index=models.SparseIndexParams(on_disk=False))
                                   },
                                   )
        qdrant = QdrantVectorStore(
            client=client,
            collection_name=self.collection_name,
            sparse_embedding=sparse_embeddings,
            retrieval_mode=RetrievalMode.SPARSE,
            sparse_vector_name="sparse",
            )
        return qdrant
    
    def vector_qdrant_hybrid(self) -> QdrantVectorStore:
        sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
        client = QdrantClient(path=self.path)
        client.create_collection(
            collection_name=self.collection_name,
            vectors_config={"dense": VectorParams(size=3072, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams(index=models.SparseIndexParams(on_disk=False))
                                   },
                                   )
        qdrant = QdrantVectorStore(
            client=client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
            sparse_embedding=sparse_embeddings,
            retrieval_mode=RetrievalMode.HYBRID,
            vector_name="dense",
            sparse_vector_name="sparse",
            )
        return qdrant