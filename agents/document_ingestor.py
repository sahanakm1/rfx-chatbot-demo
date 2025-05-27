# agents/document_ingestor.py

from agents.embedding_utils import split_text
from agents.vector_store import get_cached_vector_store
from agents.llm_calling import llm_calling
from langchain_core.documents import Document
import hashlib

# Keep track of which vector collections have already been created to avoid redundant recreations
_created_collections = set()


# Ingest a document by splitting, embedding, and storing its chunks in a vector DB
def ingest_document(
    doc_id_prefix: str,
    documents: list[Document],
    collection_name: str = "rfx_classification"
) -> str:

    # Validate input
    if not documents:
        raise ValueError("No documents provided for ingestion.")

    embed_model = llm_calling().call_embed_model()

    force_recreate = False
    if collection_name not in _created_collections:
        force_recreate = True
        _created_collections.add(collection_name)

    vector_db = get_cached_vector_store(
        collection_name=collection_name,
        embeddings=embed_model,
        ensure_exists=True,
        force_recreate=force_recreate
    )

    doc_hashes = []

    for i, doc in enumerate(documents):
        doc_name = doc_id_prefix
        doc_id = f"{doc_id_prefix}_part_{i+1}"
        content = doc.page_content.strip()
        if not content:
            continue

        doc_hash = hashlib.md5(doc_id.encode("utf-8")).hexdigest()
        doc_hashes.append(doc_hash)

        # Fragmentación si es necesario
        if len(content.split()) < 500:
            chunks = [Document(page_content=content, metadata={**doc.metadata, "source": doc_name})]
        else:
            chunks = split_text(content)
            for chunk in chunks:
                chunk.metadata = {**doc.metadata, "source": doc_name}

        vector_db.add_documents(chunks)

    return doc_hashes
