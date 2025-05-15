# brief_node.py
# Handles the creation and progressive completion of the brief structure.

from agents.brief_intake_agent import run_brief_intake, try_auto_answer_batch, retrieval_context, update_brief_with_user_response
from agents.chat_agent import generate_question_for_section
from prompts.brief_structure import SECTION_TITLES 


def brief_node(state):
    print("\n---brief node---")
    print("\t\t---next_action---", state.get("next_action", ""))
    print("\t\t---user_input---", state.get("user_input", ""))

    rfx_type = state.get("rfx_type")
    user_input = (state.get("user_input") or "").strip()
    texts = state.get("uploaded_texts", [])
    doc_name = state.get("doc_name", "TEMP")
    collection = state.get("collection_name", "")

    # Initialize list to track which sections failed auto-generation
    if "unanswerable_sections" not in state:
        state["unanswerable_sections"] = []

    # Step 1: If no brief exists, initialize it
    if not state.get("brief"):
        print("\t---brief node--- run brief initialization")
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

    # Step 2: If the user just answered a pending question, record it
    elif state.get("pending_question") and user_input:
        print("\t---brief node--- processing user response to pending question")
        update_brief_with_user_response(state, user_input)
        state["brief_updated"] = True
        state["user_input"] = None

    # Step 3: Try to resolve up to 5 missing sections in parallel using threading
    # Do not retry sections already deemed unanswerable by the model
    unresolved_set = set(state.get("unanswerable_sections", []))
    remaining = [pair for pair in state.get("missing_sections", []) if pair not in unresolved_set]

    if remaining and state['next_action'] != "start_brieft":
        batch = remaining[:3]  # Process 5 sections at a time
        print("\t---brief node--- try auto answer batch mode")
        resolved, unresolved = try_auto_answer_batch(state, batch)
        print("\t---brief node--- resolved answers: "+str(len(resolved)))
        print("\t---brief node--- unresolved answers: "+str(len(unresolved)))

        
        for (section, sub), answer in resolved.items():
            # Get the user-friendly titles
            section_title = SECTION_TITLES.get(section, section)
            
            # Fetch the subsection title from state["brief"] if available
            sub_title = state.get("brief", {}).get(section, {}).get(sub, {}).get("title", sub)

            # Add concise message to chat
            state["chat_history"].append({
                "role": "assistant",
                "content": f"✅ Section **{section_title}.{sub_title}** is generated and ready for review"
            })

            # state["chat_history"].append({
            #     "role": "assistant",
            #     "content": f"✅ Filled section **{section}.{sub}** from uploaded documents:\n\n{answer}"
            # })

        if resolved:
            state["brief_updated"] = True

        # Remove resolved from missing_sections
        state["missing_sections"] = [pair for pair in state["missing_sections"] if pair not in resolved]

        # Append unresolved to a permanent list to avoid retrying them
        state["unanswerable_sections"].extend(unresolved)

        # Ask user about the first unresolved if there’s none pending yet
        if unresolved:
            section, sub = unresolved[0]
            question = state["brief"][section][sub]["question"]
            state["pending_question"] = {"section": section, "sub": sub, "question": question, "asked": False}
            state["next_action"] = "ask_user_brief_question"
        else:
            # All batch items were successfully answered, continue to next round
            state["pending_question"] = None
            state["next_action"] = "ask_brief_question"

    # Final step: if no missing sections remain
    elif not state.get("missing_sections"):
        print("\t---brief node--- no more missing sections")
        state["pending_question"] = None
    else:
        state['next_action'] = "ask_brief_question"

    return state
