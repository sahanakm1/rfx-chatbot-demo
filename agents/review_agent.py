# agents/review_agent.py
from agents.llm_calling import llm_calling
import re

def handle_review_feedback(state, user_comment: str):
    brief = state.get("brief", {})
    llm = llm_calling().call_llm()

    # Step 1: Try to find which section the user is referring to
    candidates = []
    for section, subs in reversed(list(brief.items())):
        for sub, content in subs.items():
            original = content.get("answer", "")
            prompt = f"""
                        You are helping a user refine a document section based on a comment.

                        Section content:
                        {original}

                        User comment:
                        {user_comment}

                        Does this comment relate to this content? Reply with "YES" or "NO".
                    """
            response = llm.invoke(prompt).content.strip().upper()
            if "YES" in response:
                candidates.append((section, sub, original))

    if not candidates:
        return False, None, None

    section, sub, original = candidates[0]  # Pick first valid match

    # Step 2: Rewrite the selected content using user feedback
    prompt = f"""
                Rewrite the following section incorporating the user's feedback.
                Use business-appropriate language, typical of procurement or vendor evaluation scenarios.
                Keep the tone professional, respectful, and helpful — tailored for a procurement team or business stakeholder.

                Original content:
                {original}

                User feedback:
                {user_comment}

                
                Please rewrite original content using the user's feedback in a way that is more complete, polished, and aligned with the brief’s purpose. 
                Do not use the first person.
                Only output the refined revised content, no explanation.
            """
    new_answer = llm.invoke(prompt).content.strip()
    state["brief"][section][sub]["answer"] = new_answer
    return True, section, sub
