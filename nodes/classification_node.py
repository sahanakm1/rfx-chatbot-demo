# classification_node.py
# Uses document or user input to determine RFx type and notifies the user if classification is successful.

from agents.classification_agent import classify_rfx
from agents.chat_agent import append_rfx_comment

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

        # Directly notify the user about the classification result
        if state["rfx_type"] != "Unknown" and not state.get("rfx_notified"):
            rfx_comment = append_rfx_comment(state, "")
            state["chat_history"].append({"role": "assistant", "content": rfx_comment})
            state["rfx_notified"] = True

    except Exception as e:
        state["rfx_type"] = "Unknown"
        state.setdefault("logs", []).append(f"[Error] Classification failed: {e}")

    # Remove trigger_chat as it's no longer needed
    state.pop("trigger_chat", None)
    state["user_input"] = None
    return state
