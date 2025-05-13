# orchestrator_router.py
# Decides which agent/node to activate next based on current state.

def orchestrator_router(state):
    print("[router] state keys:", state.keys())

    if state.get("pending_question") and state.get("user_input"):
        print("[router] User replied to a pending question → brief_intake_agent")
        return "brief_intake_agent"

    if not state.get("rfx_type") and (state.get("user_input") or state.get("uploaded_texts")):
        print("[router] Need to classify RFx type → classification_agent")
        return "classification_agent"

    if state.get("rfx_type") and not state.get("brief"):
        print("[router] Generating initial brief → brief_intake_agent")
        return "brief_intake_agent"

    if state.get("pending_question"):
        print("[router] Asking user a pending question → chat_agent")
        return "chat_agent"

    if state.get("brief") and not state.get("document_generated"):
        print("[router] Ready to draft document → draft_generator")
        return "draft_generator"

    if state.get("user_input") and not state.get("rfx_type"):
        print("[router] General message → chat_agent")
        return "chat_agent"

    return "end"
