# 📁 File: nodes/review_node.py
from agents.review_agent import handle_review_feedback
from prompts.brief_structure import SECTION_TITLES

def review_agent_node(state):
    print("[review_agent_node] Starting brief review phase")

    user_input = state.get("user_input") or ""
    user_input = user_input.strip()

    print("[review_agent_node] user_input: "+ user_input)

    
    # If user_input is empty, and review hasn't started, show the initial message
    if not user_input and not state.get("review_intro_shown"):
        state["chat_history"].append({
            "role": "assistant",
            "content": (
                "🎯 Your brief is ready! Please review the generated content in the right panel.\n\n"
                "If you'd like to revise or improve any section, just type your comments here — for example, "
                "\"Update the evaluation criteria to include delivery time\".\n\n"
                "If everything looks good, just say 'all good' or 'no changes'."
            )
        })
        state["review_intro_shown"] = True
        state["next_action"] = "review_feedback_phase"
        return state

    # Case 1: User says it's all good
    if user_input.lower() in ["all good", "no changes"]:
        print("[review_agent_node] case 1: user confirmed all is good")
        state["next_action"] = "draft_generator"
        state["finish_review"] = True
        state["user_input"] = ""
        return state

    # Case 2: User gave a comment
    if user_input:
        updated, section, sub = handle_review_feedback(state, user_input)
        print(f"[review_agent_node] case 2: section: {section or 'N/A'} subsection: {sub or 'N/A'}")

        if updated:
            #section_key = f"{section}.{sub}" if sub else section
            section_title = SECTION_TITLES.get(section, section)
            sub_title = state["brief"].get(section, {}).get(sub, {}).get("title", sub)
            full_title = f"{section_title}.{sub_title}"

            state["chat_history"].append({
                "role": "assistant",
                "content": f"✏️ I've updated **{full_title}** based on your feedback. You can continue reviewing or tell me it's all good to proceed."
            })
        else:
            state["chat_history"].append({
                "role": "assistant",
                "content": "❓I couldn't identify which section you're referring to. Could you clarify, please?"
            })

        state["user_input"] = None
        state["next_action"] = "review_feedback_phase"
        return state

    # Default fallback
    print("[review_agent_node] No actionable user input yet.")

    return state
