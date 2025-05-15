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
        state["next_action"] = ""
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
    if user_input and (not state.get("pending_question") or not state["pending_question"].get("asked")):
        print("\t---chat node---normal message")

        # ✅ If user is clarifying request type manually
        if state.get("next_action") == "wait_user_rfx_type":
            user_reply = user_input.lower()

            if "rfp" in user_reply:
                state["rfx_type"] = "RFP"
            elif "rfq" in user_reply:
                state["rfx_type"] = "RFQ"
            elif "rfi" in user_reply:
                state["rfx_type"] = "RFI"
            else:
                state["chat_history"].append({
                    "role": "assistant",
                    "content": "Could you confirm if your request is an RFP, RFQ, or RFI?"
                })
                state["user_input"] = None
                return state

            state["chat_history"].append({
                "role": "assistant",
                "content": f"Thanks! I've updated this to a **{state['rfx_type']}**. Let me guide you through generating the brief, section by section — the generated content will appear in the right panel for your review."
            })
            state["next_action"] = "start_brieft"
            state["user_input"] = None
            return state

        # ✅ Handle confirmation after classification
        if state.get("next_action") == "wait_after_classification":
            user_reply = user_input.lower()
            positive_responses = ["yes", "sure", "ok", "go ahead", "continue", "proceed", "sounds good", "help with rfx"]
            negative_responses = ["no", "not really", "change", "different", "wrong", "don’t think"]
            vague_responses = ["not sure", "maybe", "i don’t know", "idk", "unclear", "confused", "need help", "could be"]

            if any(p in user_reply for p in positive_responses):
                print("\t---chat node---positive confirmation -> start brief")
                state["chat_history"].append({
                    "role": "assistant",
                    "content": "Thanks for confirming! Let me guide you through generating the brief, section by section — the generated content will appear in the right panel for your review. "
                })
                state["next_action"] = "start_brieft"
                state["user_input"] = None
                return state

            elif any(n in user_reply for n in negative_responses + vague_responses):
                print("\t---chat node---user rejected or unsure → provide guidance")
                state["chat_history"].append({
                    "role": "assistant",
                    "content": """No problem! Here's a quick reference to help you decide:

- **RFP** – Request for Proposal: when you're looking for full solutions or custom proposals  
- **RFQ** – Request for Quotation: when you're asking for pricing or cost estimates  
- **RFI** – Request for Information: when you're exploring options or vendor capabilities

Which one sounds most relevant for your request?"""
                })
                state["next_action"] = "wait_user_rfx_type"
                state["user_input"] = None
                return state

        # Default fallback to LLM conversation
        response = handle_conversation(state, user_input)
        state["llm_response"] = response
        state["chat_history"].append({"role": "assistant", "content": response})
        state["user_input"] = None
        return state

    return state