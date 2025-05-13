# chat_node.py
# Handles general or fallback LLM responses, and notifies user of RFx type when appropriate.

from agents.chat_agent import handle_conversation, append_rfx_comment
from agents.brief_intake_agent import update_brief_with_user_response

def chat_node(state):
    print("---chat node---")
    user_input = state.get("user_input") or ""
    user_input = user_input.strip()

    if state.get("pending_question"):
        # This is handled by brief_node, so chat_node should skip processing
        return state

    if state.get("rfx_type") and not state.get("rfx_notified"):
        # Inform user of detected RFx type (only once)
        rfx_comment = append_rfx_comment(state, "")
        state["llm_response"] = rfx_comment
        state["chat_history"].append({"role": "assistant", "content": rfx_comment})
        state["rfx_notified"] = True
        return state

    if user_input:
        # Normal message processing
        response = handle_conversation(state, user_input)
        state["llm_response"] = response
        state["chat_history"].append({"role": "assistant", "content": response})
        state["user_input"] = None

    elif not state.get("rfx_notified"):
        # Only fallback if no user input and rfx type hasn't been notified
        fallback = "I'm here if you need help with your RFx request."
        state["llm_response"] = fallback
        state["chat_history"].append({"role": "assistant", "content": fallback})

    return state
