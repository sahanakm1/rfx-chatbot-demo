from agents.embedding_utils import split_text
from agents.vector_store import vector_store
from agents.rag_classifier import classify_with_rag
from agents.intent_classifier import classify_by_intent
from agents.llm_calling import llm_calling
from langchain_core.documents import Document
import hashlib
import time

_doc_cache = {}

def classify_rfx(text: str = "", user_input: str = "", model_name: str = "mistral", collection_name: str = "rfx_classification") -> dict:
    if not user_input.strip() and not text.strip():
        log_msgs = ["[INFO] No user input or document provided. Skipping classification."]
        return {"rfx_type": "Unknown", "logs": log_msgs}

    log_msgs = []
    if text.strip():
        doc_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        if doc_hash in _doc_cache:
            vector_db = _doc_cache[doc_hash]
            log_msgs.append("[INFO] Using cached vector DB for document")
        else:
            log_msgs.append("[INFO] Starting classification using document (RAG mode)...")
            if len(text.split()) < 500:
                chunks = [Document(page_content=text)]
                log_msgs.append("[INFO] Document is short. Using full text as a single chunk.")
            else:
                start_chunking = time.time()
                chunks = split_text(text)
                chunks = chunks[:3]
                print("[TIMING] Text splitting and truncation started")
                log_msgs.append("[STEP] Splitting and truncating text")
            log_msgs.append("[STEP] Splitting and truncating text")

            llm = llm_calling(model_name=model_name)
            embed_model = llm.call_embed_model()

            start = time.time()
            vectors = embed_model.embed_documents([chunk.page_content for chunk in chunks])
            print(f"[TIMING] Embedding {len(vectors)} chunks took {time.time() - start:.2f}s")
            log_msgs.append("[STEP] Creating embeddings")

            store = vector_store(collection_name=collection_name, embeddings=embed_model, path="./qdrant_store")
            start_store = time.time()
            vector_db = store.vector_qdrant_dense(create_if_not_exists=True, force_recreate=False)
            print(f"[TIMING] Qdrant store init took {time.time() - start_store:.2f}s")
            log_msgs.append("[STEP] Initializing Qdrant vector store")
            docs = [Document(page_content=chunk.page_content) for chunk in chunks]

            start_add = time.time()
            vector_db.add_documents(docs)
            print(f"[TIMING] Adding documents to Qdrant took {time.time() - start_add:.2f}s")
            log_msgs.append("[STEP] Adding documents to vector DB")
            _doc_cache[doc_hash] = vector_db

        rfx_type = classify_with_rag(vector_db, user_input, model_name=model_name)
        return {"rfx_type": rfx_type, "logs": log_msgs}

    else:
        log_msgs.append("[INFO] No document provided. Using intent classification...")
        rfx_type = classify_by_intent(user_input, model_name=model_name)
        return {"rfx_type": rfx_type, "logs": log_msgs}