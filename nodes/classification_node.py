
# classification_node.py
# Uses document or user input to determine RFx type.

from agents.classification_agent import classify_rfx

def classification_node(state):
    user_input = state.get("user_input", "").strip()
    collection = state.get("collection_name", "")
    uploaded = state.get("uploaded_texts", [])

    if not user_input and not uploaded:
        state["rfx_type"] = "Unknown"
        state.setdefault("logs", []).append("[Warning] No input or documents provided for classification.")
        return state

    try:
        result = classify_rfx(
            user_input=user_input,
            collection_name=collection,
            uploaded_texts=uploaded,
        )
        state["rfx_type"] = result.get("rfx_type", "Unknown")

        # Trigger chat notification if classification succeeded
        state["trigger_chat"] = True if state["rfx_type"] != "Unknown" else False

    except Exception as e:
        state["rfx_type"] = "Unknown"
        state.setdefault("logs", []).append(f"[Error] Classification failed: {e}")

    state["user_input"] = None
    return state