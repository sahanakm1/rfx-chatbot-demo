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
    doc_id: str, 
    text: str, 
    collection_name: str = "rfx_classification"
) -> str:

    # Validate input
    if not text or not text.strip():
        raise ValueError(f"Document '{doc_id}' is empty, skipping ingestion.")

    # Generate a unique hash for the document
    doc_hash = hashlib.md5(doc_id.encode("utf-8")).hexdigest()

    # If document is short, keep it as a single chunk
    if len(text.split()) < 500:
        chunks = [Document(page_content=text)]
    else:
        chunks = split_text(text)

    # Ensure we have chunks to store
    if not chunks:
        raise ValueError(f"Document '{doc_id}' produced no valid chunks.")

    # Load embedding model
    #embed_model = llm_calling(model_name=model_name).call_embed_model()
    embed_model = llm_calling().call_embed_model()

    # Only force recreate the collection if it hasn't been created before in this session
    force_recreate = False
    if collection_name not in _created_collections:
        force_recreate = True
        _created_collections.add(collection_name)

    # Get or create the vector store
    vector_db = get_cached_vector_store(
        collection_name=collection_name,
        embeddings=embed_model,
        ensure_exists=True,
        force_recreate=force_recreate
    )

    # Store the document chunks in the vector DB
    docs = [Document(page_content=chunk.page_content) for chunk in chunks]
    vector_db.add_documents(docs)

    return doc_hash  # Return the document identifier (hash)
