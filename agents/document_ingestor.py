# agents/document_ingestor.py

from agents.embedding_utils import split_text
from agents.vector_store import get_cached_vector_store
from agents.llm_calling import llm_calling
from langchain_core.documents import Document
import hashlib


_created_collections = set()  # ← para evitar recreaciones múltiples


def ingest_document(doc_id: str, text: str, model_name: str = "mistral", collection_name: str = "rfx_classification") -> str:

    if not text or not text.strip():
        raise ValueError(f"Document '{doc_id}' is empty, skipping ingestion.")

    doc_hash = hashlib.md5(doc_id.encode("utf-8")).hexdigest()

    if len(text.split()) < 500:
        chunks = [Document(page_content=text)]
    else:
        chunks = split_text(text)

    if not chunks:
        raise ValueError(f"Document '{doc_id}' produced no valid chunks.")

    embed_model = llm_calling(model_name=model_name).call_embed_model()

    # Solo forzar recreación si es la primera vez que vemos esta colección
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

    docs = [Document(page_content=chunk.page_content) for chunk in chunks]
    vector_db.add_documents(docs)

    return doc_hash