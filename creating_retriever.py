import os
from uuid import uuid4
import shutil

from data_preprocessing import data_preprocessing
from langchain_qdrant import QdrantVectorStore
from agents.vector_store import vector_store


def file_names(directory):
    files = []
    for file in os.listdir(directory):
        if file.endswith(".pdf"):
            files.append(os.path.join(directory, file))
    return files


def langchain_doc_creation(file_path):
    doc = []
    for f in file_path:
        dp = data_preprocessing(file_path=f)
        doc += dp.load_data()
    return doc


class universal_retrieval():
    def __init__(self, embeddings, collection_name, path):
        self.embeddings = embeddings
        self.collection_name = collection_name
        self.path = path

    def load_existing_vdb_collection(self):
        # Force-delete old vectorstore if exists
        collection_path = os.path.join(self.path, "collection", self.collection_name)
        if os.path.exists(collection_path):
            shutil.rmtree(collection_path)

        store = vector_store(
            collection_name=self.collection_name,
            embeddings=self.embeddings,
            path=self.path
        )
        vs_dense = store.vector_qdrant_dense(create_if_not_exists=True, force_recreate=True)
        return vs_dense.as_retriever(search_type="similarity", search_kwargs={"k": 3})


class user_retriever():
    def __init__(self, embeddings, collection_name, path, doc_input, type_of_retrieval="dense"):
        self.type_of_retrieval = type_of_retrieval
        self.embeddings = embeddings
        self.collection_name = collection_name
        self.path = path
        self.doc_input = doc_input

    def create_new_vdb(self):
        if self.type_of_retrieval == "dense":
            vs_dense = vector_store(
                collection_name=self.collection_name,
                embeddings=self.embeddings,
                path=self.path
            ).vector_qdrant_dense(force_recreate=True)
        elif self.type_of_retrieval == "sparse":
            vs_dense = vector_store(
                collection_name=self.collection_name,
                embeddings=self.embeddings,
                path=self.path
            ).vector_qdrant_sparse()
        else:
            vs_dense = vector_store(
                collection_name=self.collection_name,
                embeddings=self.embeddings,
                path=self.path
            ).vector_qdrant_hybrid()

        uuids = [str(uuid4()) for _ in range(len(self.doc_input))]
        vs_dense.add_documents(documents=self.doc_input, ids=uuids)
        return vs_dense.as_retriever(search_type="similarity", search_kwargs={"k": 3})