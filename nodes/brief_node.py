# brief_node.py
# Handles the creation and progressive completion of the brief structure.

from agents.brief_intake_agent import run_brief_intake, try_auto_answer, retrieval_context
from agents.chat_agent import generate_question_for_section

def brief_node(state):
    print("\n---brief node---")
    rfx_type = state.get("rfx_type")
    user_input = state.get("user_input", "").strip()
    texts = state.get("uploaded_texts", [])
    doc_name = state.get("doc_name", "TEMP")
    collection = state.get("collection_name", "")

    # Step 1: If no brief exists, initialize it
    if not state.get("brief"):
        print("\t---brief node--- run brief initialization")
        brief, missing, disclaimer = run_brief_intake(
            rfx_type=rfx_type,
            user_input=user_input,
            uploaded_texts=texts,
            doc_name=doc_name,
            collection_name=collection,
        )
        state["brief"] = brief
        state["missing_sections"] = missing
        state["disclaimer"] = disclaimer

    # Step 2: If the user just answered a pending question, record it
    elif state.get("pending_question") and user_input:
        print("\t---brief node--- processing user response to pending question")
        section = state["pending_question"]["section"]
        sub = state["pending_question"]["sub"]
        state["brief"][section][sub]["answer"] = user_input
        state["missing_sections"] = [pair for pair in state["missing_sections"] if pair != (section, sub)]
        state["brief_updated"] = True
        state["user_input"] = None  # Limpiar después de guardar
        state["pending_question"] = None

    # Step 3: Process the next pending section if available
    if state.get("missing_sections"):
        section, sub = state["missing_sections"][0]
        question = state["brief"][section][sub]["question"]

        # Try to auto-answer with RAG first
        auto_answered = False
        if retrieval_context["qa_chain"]:
            print("\t---brief node--- trying auto-answer via RAG")
            answer = try_auto_answer(state)
            if answer != "N/A":
                state["chat_history"].append({
                    "role": "assistant",
                    "content": f"\u2705 Filled section **{section}.{sub}** from uploaded documents:\n\n{answer}"
                })
                state["brief_updated"] = True
                auto_answered = True

        # If not auto-answered, ask the user
        if not auto_answered:
            print("\t---brief node--- could not auto-answer, asking user")
            state["pending_question"] = {"section": section, "sub": sub, "question": question, "asked": False}
            state["next_action"] = "ask_brief_question"

    else:
        print("\t---brief node--- no more missing sections")
        state["pending_question"] = None

    state["user_input"] = None

    return state
