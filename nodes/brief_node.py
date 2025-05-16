# brief_node.py
# Handles the creation and progressive completion of the brief structure.

from agents.brief_intake_agent import run_brief_intake, try_auto_answer_batch, update_brief_with_user_response
from prompts.brief_structure import SECTION_TITLES

def brief_node(state):
    print("\n---brief node---")
    print("Next action:", state.get("next_action"))
    print("User input:", state.get("user_input"))

    rfx_type = state.get("rfx_type")
    user_input = (state.get("user_input") or "").strip()
    texts = state.get("uploaded_texts", [])
    doc_name = state.get("doc_name", "TEMP")
    collection = state.get("collection_name", "")

    if "unanswerable_sections" not in state:
        state["unanswerable_sections"] = []

    # Step 1: Initialize brief if not already created
    if not state.get("brief"):
        brief, missing, pending, disclaimer = run_brief_intake(
            rfx_type=rfx_type,
            user_input=user_input,
            uploaded_texts=texts,
            doc_name=doc_name,
            collection_name=collection,
        )
        state["brief"] = brief
        state["missing_sections"] = missing
        state["disclaimer"] = disclaimer
        state["pending_question"] = pending
        state["user_input"] = None
        state["next_action"] = "ask_brief_question"
        return state

    # Step 2: Save user response to pending question
    if state.get("pending_question") and user_input:
        update_brief_with_user_response(state, user_input)
        state["brief_updated"] = True
        state["user_input"] = None

    # Step 3: Try answering next batch of sections
    unresolved_set = set(state.get("unanswerable_sections", []))
    remaining = sorted([pair for pair in state.get("missing_sections", []) if pair not in unresolved_set])

    if remaining:
        batch = remaining[:3]
        resolved, unresolved = try_auto_answer_batch(state, batch)

        for (section, sub), answer in resolved.items():
            section_title = SECTION_TITLES.get(section, section)
            sub_title = state["brief"][section][sub]["title"]
            state["chat_history"].append({
                "role": "assistant",
                "content": f"✅ Section **{section_title}.{sub_title}** is generated and ready for review"
            })
            state["brief_updated"] = True

        state["missing_sections"] = [pair for pair in state["missing_sections"] if pair not in resolved]
        state["unanswerable_sections"].extend(unresolved)

        # Step 4: Set next manual question if unresolved remains
        if unresolved:
            section, sub = unresolved[0]
            question = state["brief"][section][sub]["question"]
            state["pending_question"] = {"section": section, "sub": sub, "question": question, "asked": False}
            state["next_action"] = "ask_user_brief_question"
        # Step 5: If all done, proceed to generate document
        elif not state["missing_sections"]:
            state["pending_question"] = None
            state["next_action"] = "draft_generator"
        else:
            state["pending_question"] = None
            state["next_action"] = "ask_brief_question"

    # Final check: if all answered and brief exists, go to draft
    elif not state.get("missing_sections") and state.get("brief"):
        state["pending_question"] = None
        state["next_action"] = "draft_generator"

    return state