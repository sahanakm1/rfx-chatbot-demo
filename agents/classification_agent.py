# agents/classification_agent.py

from agents.vector_store import get_cached_vector_store
from agents.rag_classifier import classify_with_rag
from agents.intent_classifier import classify_by_intent
from agents.llm_calling import llm_calling


def classify_rfx(user_input: str = "", collection_name: str = "", model_name: str = "mistral",
                 uploaded_texts: list = None, log_callback=None) -> dict:
    log_msgs = []

    def log(msg):
        if msg not in log_msgs:
            log_msgs.append(msg)
            if log_callback and "[TIMING]" not in msg:
                clean_msg = msg.replace("[INFO]", "").replace("[STEP]", "").strip()
                log_callback(clean_msg)

    if not user_input.strip():
        log("[INFO] No input provided for classification.")
        return {"rfx_type": "Unknown", "logs": log_msgs}

    if uploaded_texts:  # SOLO si hay documentos subidos
        try:
            log("[INFO] Using RAG-based classification (vector store)")
            #embed_model = llm_calling(model_name=model_name).call_embed_model()
            #vector_db = get_cached_vector_store(collection_name=collection_name, embeddings=embed_model)
            #rfx_type = classify_with_rag(vector_db, user_input, model_name=model_name)
            rfx_type = classify_by_intent("\n\n".join([doc["content"] for doc in uploaded_texts]), model_name=model_name)
        except Exception as e:
            log(f"[ERROR] Falló la clasificación con vector DB: {e}")
            log("[INFO] Reintentando con clasificación por intención...")
            rfx_type = classify_by_intent(user_input, model_name=model_name)
    else:
        log("[INFO] No documents uploaded. Using intent classification...")
        rfx_type = classify_by_intent(user_input, model_name=model_name)

    return {"rfx_type": rfx_type, "logs": log_msgs}