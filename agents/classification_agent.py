# agents/classification_agent.py
from agents.embedding_utils import split_text
from agents.vector_store import vector_store
from agents.rag_classifier import classify_with_rag
from agents.intent_classifier import classify_by_intent
from agents.llm_calling import llm_calling
from langchain_core.documents import Document
import hashlib

_doc_cache = {}

def classify_rfx(text=None, user_input: str = "", model_name: str = "mistral",
                 collection_name: str = "rfx_classification", log_callback=None) -> dict:
    log_msgs = []

    def log(msg):
        if msg not in log_msgs:
            log_msgs.append(msg)
            if log_callback and "[TIMING]" not in msg:
                clean_msg = msg.replace("[INFO]", "").replace("[STEP]", "").strip()
                log_callback(clean_msg)

    if not (user_input or "").strip() and not text:
        log("[INFO] No user input or document provided. Skipping classification.")
        return {"rfx_type": "Unknown", "logs": log_msgs}

    # Normalize text to string
    use_text = ""
    if isinstance(text, str):
        use_text = text.strip()
    elif isinstance(text, list) and all(isinstance(d, Document) for d in text):
        use_text = "\n\n".join(d.page_content for d in text).strip()

    if use_text:
        doc_hash = hashlib.md5(use_text.encode("utf-8")).hexdigest()
        if doc_hash in _doc_cache:
            vector_db = _doc_cache[doc_hash]
            log("[INFO] Using cached vector DB for document")
        else:
            log("[INFO] Starting classification using document (RAG mode)...")
            if len(use_text.split()) < 500:
                chunks = [Document(page_content=use_text)]
                log("[INFO] Document is short. Using full text as a single chunk.")
            else:
                chunks = split_text(use_text)[:3]
                log("[STEP] Splitting and truncating text")

            llm = llm_calling(model_name=model_name)
            embed_model = llm.call_embed_model()
            log("[STEP] Creating embeddings")
            vectors = embed_model.embed_documents([chunk.page_content for chunk in chunks])

            store = vector_store(collection_name=collection_name, embeddings=embed_model, path="./qdrant_store")
            log("[INFO] Connecting to Qdrant collection: rfx_classification")
            vector_db = store.vector_qdrant_dense(create_if_not_exists=True, force_recreate=True)
            docs = [Document(page_content=chunk.page_content) for chunk in chunks]
            log("[STEP] Adding documents to vector DB")
            vector_db.add_documents(docs)

            _doc_cache[doc_hash] = vector_db

        rfx_type = classify_with_rag(vector_db, user_input, model_name=model_name)
        return {"rfx_type": rfx_type, "logs": log_msgs}

    else:
        log("[INFO] No document provided. Using intent classification...")
        rfx_type = classify_by_intent(user_input, model_name=model_name)
        return {"rfx_type": rfx_type, "logs": log_msgs}