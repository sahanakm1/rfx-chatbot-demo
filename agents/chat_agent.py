# agents/chat_agent.py

def generate_question_for_section(section: str) -> str:
    """
    Generate a user-facing question based on the missing section name.
    """
    print(section)
    questions = {
        "context": "Could you describe the background or context of this request?",
        "goals": "What are the primary objectives you're aiming to achieve?",
        "deliverables": "What specific outputs or deliverables are expected?",
        "dates": "What are the important dates or deadlines to consider?"
    }
    return section['question']
