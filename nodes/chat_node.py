from agents.brief_intake_agent import update_brief_with_user_response
from agents.chat_agent import append_rfx_comment, generate_question_for_section, handle_conversation
from agents.llm_calling import llm_calling

def chat_node(state):
    print("---chat node---")
    user_input = state.get("user_input") or ""
    user_input = user_input.strip()

    print("User input:", user_input)
    print("Next action:", state.get("next_action"),"")

    vague_responses = [
        "not sure", "maybe", "i don’t know", "idk", "unclear",
        "confused", "need help", "could be", "need more info", "explain"
    ]

    llm = llm_calling().call_llm()

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

        if state.get("next_action") == "wait_user_rfx_type":
            user_reply = user_input.lower()

            if "rfp" in user_reply:
                state["rfx_type"] = "RFP"
            elif "rfq" in user_reply:
                state["rfx_type"] = "RFQ"
            elif "rfi" in user_reply:
                state["rfx_type"] = "RFI"
            elif any(v in user_reply for v in vague_responses):
                clarification_prompt = f"""
                The user is still unsure after reading the earlier explanation.
                Please re-explain the differences between RFI, RFQ, and RFP briefly (3–4 lines max),
                but give relatable examples or context this time.
                End with a single follow-up question asking which they'd like to proceed with.
                """
                response = llm.invoke([{"role": "user", "content": clarification_prompt}])
                state["chat_history"].append({"role": "assistant", "content": response.content.strip()})
                state["user_input"] = None
                return state
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
            state["next_action"] = "wait_after_classification_confirmation"
            return state

        if state.get("next_action") == "wait_after_classification":
            user_reply = user_input.lower()
            positive_responses = ["yes", "sure", "ok", "go ahead", "continue", "proceed", "sounds good", "help with rfx"]
            negative_responses = ["no", "not really", "change", "different", "wrong", "don’t think"]
            if any(p in user_reply for p in positive_responses):
                print("\t---chat node---positive confirmation -> start brief")
                state["chat_history"].append({
                    "role": "assistant",
                    "content": "Thanks for confirming! Let me guide you through generating the brief, section by section — the generated content will appear in the right panel for your review. "
                })
                state["next_action"] = "wait_after_classification_confirmation"
                state["user_input"] = None
                return state
            elif any(n in user_reply for n in negative_responses + vague_responses):
                print("\t---chat node---user rejected or unsure → provide LLM clarification")
                clarification_prompt = f"""
                The assistant previously classified this request as {state.get("rfx_type", "Unknown")},
                but the user disagreed or was unsure. Now explain the three types of RFx (RFP, RFQ, RFI)
                in a friendly, helpful way.
                If user is unsure or gives vague responses, then explain the request types further.
                Ask the user which one they’d prefer to proceed with.

                Keep it concise (3-5 lines) and natural.
                """
                response = llm.invoke([{"role": "user", "content": clarification_prompt}])
                state["chat_history"].append({"role": "assistant", "content": response.content.strip()})
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