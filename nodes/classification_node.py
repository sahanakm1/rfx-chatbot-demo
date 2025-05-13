
# classification_node.py
# Uses document or user input to determine RFx type.

from agents.classification_agent import classify_rfx

def classification_node(state):
    user_input = state.get("user_input") or ""

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

        ## Trigger chat-based confirmation if a valid RFx type was found
        if state["rfx_type"] != "Unknown" and not state.get("rfx_notified"):
            state["next_action"] = "chat_after_classification"


    except Exception as e:
        state["rfx_type"] = "Unknown"
        state.setdefault("logs", []).append(f"[Error] Classification failed: {e}")

    print("\n----after classification----")
    print(state)
    print("--------\n")

    return state