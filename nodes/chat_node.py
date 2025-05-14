
from agents.brief_intake_agent import update_brief_with_user_response
from agents.chat_agent import append_rfx_comment, generate_question_for_section, handle_conversation

def chat_node(state):
    print("---chat node---")
    user_input = state.get("user_input") or ""
    user_input = user_input.strip()


    print("User input:", user_input)
    print("Next action:", state.get("next_action"),"")


    # 1. Reformulate and ask the pending question
    if state.get("pending_question") and not state["pending_question"].get("asked"):
        print("\t---chat node---pending_question")
        original_question = state["pending_question"]["question"]
        rewritten = generate_question_for_section(state, original_question)
        state["llm_response"] = rewritten
        state["chat_history"].append({"role": "assistant", "content": rewritten})
        state["pending_question"]["asked"] = True
        return state

    # 2. Notify user about detected RFx type
    if state.get("rfx_type") and not state.get("rfx_notified"):
        print("\t---chat node---rfx_type")
        rfx_comment = append_rfx_comment(state, "")
        state["llm_response"] = rfx_comment
        state["chat_history"].append({"role": "assistant", "content": rfx_comment})
        state["rfx_notified"] = True
        state["next_action"] = "wait_after_classification"  
        return state

    # 3. If no pending question, handle general message
    # 3. Normal input (solo si no está respondiendo a una pregunta pendiente)
    if user_input and (not state.get("pending_question") or not state["pending_question"].get("asked")):
        print("\t---chat node---normal message")
        response = handle_conversation(state, user_input)
        state["llm_response"] = response
        state["chat_history"].append({"role": "assistant", "content": response})


        # Si estamos esperando confirmación tras clasificación, interpretamos este input como confirmación
        if state.get("next_action") == "wait_after_classification":
            print("\t---chat node---confirmation received after classification -> start brieft")
            state["next_action"] = "start_brieft"
            
        state["user_input"] = None

        
        return state

    # 4. Fallback
    """
    print("\t---chat node---fallback")
    fallback = "I'm here if you need help with your RFx request."
    state["llm_response"] = fallback
    state["chat_history"].append({"role": "assistant", "content": fallback})
    """
    return state
