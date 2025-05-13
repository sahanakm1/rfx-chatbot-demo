
from agents.chat_agent import generate_question_for_section, handle_conversation

def chat_node(state):
    print("---chat node---")
    user_input = state.get("user_input") or ""
    user_input = user_input.strip()

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
        from agents.chat_agent import append_rfx_comment
        rfx_comment = append_rfx_comment(state, "")
        state["llm_response"] = rfx_comment
        state["chat_history"].append({"role": "assistant", "content": rfx_comment})
        state["rfx_notified"] = True
        state["next_action"] = ""  
        return state

    # 3. If no pending question, handle general message
    # 3. Normal input (solo si no está respondiendo a una pregunta pendiente)
    if user_input and (not state.get("pending_question") or not state["pending_question"].get("asked")):
        print("\t---chat node---normal message")
        response = handle_conversation(state, user_input)
        state["llm_response"] = response
        state["chat_history"].append({"role": "assistant", "content": response})
        state["user_input"] = None  # <- clear here only for normal messages
        return state

    # 4. Fallback
    """
    print("\t---chat node---fallback")
    fallback = "I'm here if you need help with your RFx request."
    state["llm_response"] = fallback
    state["chat_history"].append({"role": "assistant", "content": fallback})
    """
    return state
