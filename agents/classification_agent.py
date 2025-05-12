# agents/classification_agent.py
from agents.intent_classifier import classify_by_intent


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
            log("[INFO] Using intent classification with document content...")
            rfx_type = classify_by_intent("\n\n".join([doc["content"] for doc in uploaded_texts]), model_name=model_name)
        except Exception as e:
            log(f"[ERROR] Falló la clasificación con vector DB: {e}")
            log("[INFO] Reintentando con clasificación por intención...")
            rfx_type = classify_by_intent(user_input, model_name=model_name)
    else:
        log("[INFO] No documents uploaded. Using intent classification...")
        rfx_type = classify_by_intent(user_input, model_name=model_name)

    return {"rfx_type": rfx_type, "logs": log_msgs}