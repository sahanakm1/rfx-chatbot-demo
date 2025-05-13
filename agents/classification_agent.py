# agents/classification_agent.py

from agents.intent_classifier import classify_by_intent

# Main function to classify the RFx type
def classify_rfx(
    user_input: str = "", 
    collection_name: str = "", 
    model_name: str = "mistral",
    uploaded_texts: list = None, 
    log_callback=None
) -> dict:
    
    log_msgs = []
    print("classify_rfx")

    # Logging helper that prevents repeated messages and formats logs
    def log(msg):
        if msg not in log_msgs:
            print(msg)
            log_msgs.append(msg)
            if log_callback and "[TIMING]" not in msg:
                clean_msg = msg.replace("[INFO]", "").replace("[STEP]", "").strip()
                log_callback(clean_msg)

    # Case: no input provided at all
    if not user_input.strip() and not uploaded_texts:
        log("[INFO] No input provided for classification.")
        return {"rfx_type": "Unknown", "logs": log_msgs}

    # Case: documents are available
    if uploaded_texts:
        try:
            log("[INFO] Using intent classification with document content...")
            # Concatenate all uploaded document contents and classify
            rfx_type = classify_by_intent(
                "\n\n".join([doc["content"] for doc in uploaded_texts]), 
                model_name=model_name
            )
        except Exception as e:
            log(f"[ERROR] Classification with vector DB failed: {e}")
            log("[INFO] Retrying with direct user input classification...")
            rfx_type = classify_by_intent(user_input, model_name=model_name)
    else:
        # Case: no documents, only classify based on user input
        log("[INFO] No documents uploaded. Using intent classification...")
        rfx_type = classify_by_intent(user_input, model_name=model_name)

    return {"rfx_type": rfx_type, "logs": log_msgs}
