# agents/consistency_checker_agent.py
from agents.llm_calling import llm_calling
from langchain_core.messages import HumanMessage

def check_consistency(state):
    """Returns 'YES' if the user response is consistent and appropriate, 'NO' otherwise."""
    llm = llm_calling().call_llm()

    pending = state.get("pending_question", {})
    history = state.get("chat_history", [])
    user_input = state.get("user_input", "").strip()

    context = "\n".join([f"{m['role']}: {m['content']}" for m in history[-4:]])
    question = pending.get("question", "")

    prompt = f"""
        #     You are verifying the consistency and relevance of a user's response.

        #     Given the previous conversation context and a question, determine if the user's most recent answer:
        #     1. Clearly relates to the question.
        #     2. Makes sense given the previous history.

        #     Return only YES or NO.

        You are verifying if a user's answer is acceptable for a given question in the context of an RFx brief.

        Say **YES** if:
        - The response is somewhat relevant to the question
        - It contains some infomation
        - It sounds like a reasonable attempt to answer (even if not perfect)

        Say **NO** only if:
        - The answer is completely unrelated
        - Or it clearly misunderstands the question
        - Or it is empty, vague, or irrelevant

        Return only YES or NO.


            Context:
            {context}

            Question:
            {question}

            User Answer:
            {user_input}
            """
    result = llm.invoke([HumanMessage(content=prompt)])
    raw = result.content.strip().upper()
    return "YES" if "YES" in raw else "NO"