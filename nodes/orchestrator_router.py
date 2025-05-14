# orchestrator_router.py
# Decides which agent/node to activate next based on current state.

from agents.chat_agent import should_trigger_classification

def orchestrator_router(state):
    print("\n----[router]----")
    

    if state.get("next_action"):
        print(f"[router] ⚠️ Repeating next_action: {state['next_action']}")

    # Reset wait_after_classification if user replied
    if state.get("wait_after_classification") and state.get("user_input"):
        print("[router] ✅ User responded after classification, clearing wait")
        state["wait_after_classification"] = False

    

    # A. User replied to a pending brief question
    if (
        state.get("user_input")
        and state.get("pending_question")
        and state["pending_question"].get("asked")
    ):
        print(state)
        print("--------\n")
        print("[router] User replied to a pending brief question → brief_intake_agent")
        return "brief_intake_agent"
    

    # B. LLM-driven readiness → classification
    elif not state.get("rfx_type") and should_trigger_classification(state):
        print(state)
        print("--------\n")
        print("[router] LLM says we're ready → classification_agent")
        return "classification_agent"

    # C. Chat follow-up after classification
    elif state.get("next_action") == "chat_after_classification":
        print(state)
        print("--------\n")
        state["next_action"] = ""
        print("[router] Post-classification notification → chat_agent")
        return "chat_agent"
    
    # D. Explicit next action: ask the user a question
    elif state.get("next_action") == "ask_brief_question":
        #print(state)
        print("--------\n")
        state["next_action"] = ""
        print("[router] Asking brief question → chat_agent")
        return "brief_intake_agent" # return "chat_agent"
    
    # D. no pudo responder el modelo, preguntar al usuario
    elif state.get("next_action") == "ask_user_brief_question":
        print(state)
        print("--------\n")
        state["next_action"] = ""
        print("[router] Asking user a brief question → chat_agent")
        return "chat_agent"

    # # D. RFx type unknown → attempt classification (if there's meaningful input or uploaded docs)
    # meaningful_input = state.get("user_input") and len(state.get("chat_history", [])) > 3
    # if not state.get("rfx_type") and (meaningful_input or state.get("uploaded_texts")):
    #     print("[router] Need to classify RFx type → classification_agent")
    #     return "classification_agent"

    
    # E. RFx type is known but brief not started → start brief
    elif state.get("next_action")=="start_brieft"  and state.get("rfx_type") and not state.get("brief")  and not state.get("pending_question") and state.get("next_action") != "wait_after_classification":
        print(state)
        print("--------\n")
        print("[router] Generating initial brief → brief_intake_agent")
        return "brief_intake_agent"
    
    # G. Default: route to chat_agent as fallback
    elif (state.get("user_input") or state.get("next_action") == "wait_after_classification") and not state.get("pending_question"):
        print(state)
        print("--------\n")
        print("[router] General message → chat_agent")
        if state.get("next_action") == "wait_after_classification": 
            print("\t----router: next action wait")
            state["next_action"] = ""
        return "chat_agent"

    # F. Document ready to be drafted
    #if state.get("brief") and not state.get("document_generated"):
    #    print("[router] Ready to draft document → draft_generator")
    #    return "draft_generator"

    

    # H. Nothing else to do
    return "end"