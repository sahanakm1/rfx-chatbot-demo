# orchestrator_router.py
# Decides which agent/node to activate next based on current state.

def orchestrator_router(state):
    print("\n----[router] state keys----")
    print(state)
    print("--------\n")

    if state.get("next_action"):
        print(f"[router] ⚠️ Repeating next_action: {state['next_action']}")



    # C. User replied to a pending brief question
    if (
        state.get("user_input")
        and state.get("pending_question")
        and state["pending_question"].get("asked")
    ):
        print("[router] User replied to a pending brief question → brief_intake_agent")
        return "brief_intake_agent"
    
    
    # A. Explicit next action: ask the user a question
    if state.get("next_action") == "ask_brief_question":
        state["next_action"] = ""
        print("[router] Asking brief question → chat_agent")
        return "chat_agent"

    # B. Chat follow-up after classification
    if state.get("next_action") == "chat_after_classification":
        state["next_action"] = ""
        print("[router] Post-classification notification → chat_agent")
        return "chat_agent"


    # D. RFx type unknown → attempt classification (if there's meaningful input or uploaded docs)
    meaningful_input = state.get("user_input") and len(state.get("chat_history", [])) > 3
    if not state.get("rfx_type") and (meaningful_input or state.get("uploaded_texts")):
        print("[router] Need to classify RFx type → classification_agent")
        return "classification_agent"

    # E. RFx type is known but brief not started → start brief
    if state.get("rfx_type") and not state.get("brief")  and not state.get("pending_question"):
        print("[router] Generating initial brief → brief_intake_agent")
        return "brief_intake_agent"

    # F. Document ready to be drafted
    if state.get("brief") and not state.get("document_generated"):
        print("[router] Ready to draft document → draft_generator")
        return "draft_generator"

    # G. Default: route to chat_agent
    if state.get("user_input") and not state.get("pending_question"):
        print("[router] General message → chat_agent")
        return "chat_agent"

    # H. Nothing else to do
    return "end"