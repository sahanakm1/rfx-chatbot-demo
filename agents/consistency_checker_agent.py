from agents.llm_calling import llm_calling
from langchain_core.messages import HumanMessage

def check_consistency(state):
    """Returns 'YES' if the response is valid, 'NO' if not, or 'REFINE' if it's acceptable but improvable."""
    llm = llm_calling().call_llm()

    pending = state.get("pending_question", {})
    history = state.get("chat_history", [])
    user_input = state.get("user_input", "").strip()

    context = "\n".join([f"{m['role']}: {m['content']}" for m in history[-4:]])
    question = pending.get("question", "")

    prompt = f"""
            You are verifying the quality of a user's answer to a question as part of completing an RFx brief.

            Your job is to classify the answer into one of **three** categories:

            🔹 **YES** → The answer is valid, clear, and appropriate.
            🔹 **REFINE** → The answer is generally correct or on-topic, but could be improved (e.g., more complete, structured, or clearer).
            🔹 **NO** → The answer is irrelevant, incorrect, vague, or does not answer the question at all.

            Use this guidance:

            ✅ Say **YES** if:
            - The answer clearly addresses the question and makes sense in context.
            - It is usable as-is, even if not perfect.

            🟡 Say **REFINE** if:
            - The answer is relevant but could benefit from improved structure, completeness, tone, or clarity.
            - It seems rushed, informal, too brief, or slightly off in focus.

            ❌ Say **NO** if:
            - The answer does not relate to the question.
            - It is too vague, completely off-topic, or clearly misunderstood.

            Return only one of these: **YES**, **REFINE**, or **NO**.

            ---

            Context:
            {context}

            Question:
            {question}

            User Answer:
            {user_input}
            """

    result = llm.invoke([HumanMessage(content=prompt)])
    response = result.content.strip().upper()

    if "YES" in response:
        return "YES"
    elif "REFINE" in response:
        return "REFINE"
    else:
        return "NO"