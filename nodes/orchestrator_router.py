# orchestrator_router.py
# Decides which agent/node to activate next based on current state.

def orchestrator_router(state):
    print("\n----[router] state keys----")
    print(state)
    print("--------\n")

    # 0. If classification completed and we need to notify user via chat
    if state.get("next_action") == "chat_after_classification":
        state.pop("next_action")
        # Ensure user_input exists to avoid NoneType error in chat_node
        state["user_input"] = ""
        print("[router] Post-classification notification → chat_agent")
        return "chat_agent"

    # 1. User has just answered a pending question → continue brief intake
    if state.get("pending_question") and state.get("user_input"):
        print("[router] User replied to a pending question → brief_intake_agent")
        return "brief_intake_agent"

    # 2. RFx type not yet classified but input or documents exist → classify -- TODO (change this logic): hardcoded force to at least has 3 messages from user
    if not state.get("rfx_type") and ((state.get("user_input") and len(state.get("chat_history", []))>5  ) or state.get("uploaded_texts")):
        print("[router] Need to classify RFx type → classification_agent")
        return "classification_agent"

    # 3. RFx type is known but no brief has been built yet → start brief generation
    if state.get("rfx_type") and not state.get("brief"):
        print("[router] Generating initial brief → brief_intake_agent")
        return "brief_intake_agent"

    # 4. There is a pending question to ask the user → continue chat
    if state.get("pending_question"):
        print("[router] Asking user a pending question → chat_agent")
        return "chat_agent"

    # 5. Brief is complete but document not yet generated → draft it
    if state.get("brief") and not state.get("document_generated"):
        print("[router] Ready to draft document → draft_generator")
        return "draft_generator"

    # 6. User input received but classification is still missing → fallback chat
    if state.get("user_input") and not state.get("rfx_type"):
        print("[router] General message → chat_agent")
        return "chat_agent"

    # 7. Nothing more to process → end
    return "end"

