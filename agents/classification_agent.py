from agents.embedding_utils import split_text
from agents.vector_store import vector_store
from agents.rag_classifier import classify_with_rag
from agents.intent_classifier import classify_by_intent
from agents.llm_calling import llm_calling
from langchain_core.documents import Document
import time

def classify_rfx(text: str = "", user_input: str = "", model_name: str = "llama3", collection_name: str = "rfx_classification") -> str:
    """
    Unified RFx classification entry point. Classifies based on document (RAG) if present,
    otherwise uses intent-based LLM classification.
    """
    if text.strip():
        print("[INFO] Starting classification using document (RAG mode)...")
        chunks = split_text(text)
        print(f"[INFO] Total text chunks created: {len(chunks)}")
        chunks = chunks[:30]  # Limit to 30 chunks max

        llm = llm_calling()
        embed_model = llm.call_embed_model()

        print("[INFO] Generating embeddings...")
        start = time.time()
        vectors = embed_model.embed_documents([chunk.page_content for chunk in chunks])
        print(f"[TIMING] Embedding {len(vectors)} chunks took {time.time() - start:.2f} sec")
        print(f"[INFO] Sample vector size: {len(vectors[0])}")

        store = vector_store(collection_name=collection_name, embeddings=embed_model, path="./qdrant_store")
        vector_db = store.vector_qdrant_dense(create_if_not_exists=True, force_recreate=False)

        print("[INFO] Converting chunks to documents...")
        docs = [Document(page_content=chunk.page_content) for chunk in chunks]

        print("[INFO] Adding pre-embedded documents to vector store...")
        vector_db.add_documents(docs, embeddings=vectors)

        print("[INFO] Running classification via RAG...")
        return classify_with_rag(vector_db, user_input)

    else:
        print("[INFO] Starting classification using user input only (Intent mode)...")
        return classify_by_intent(user_input, model_name=model_name)