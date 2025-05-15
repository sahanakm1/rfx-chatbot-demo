# agents/autorefine_agent.py
from agents.llm_calling import llm_calling
from langchain_core.messages import HumanMessage
import re

def refine_question(state):
    """Improves the question or requests clarification from the user."""
    llm = llm_calling().call_llm()

    pending = state.get("pending_question", {})
    question = pending.get("question", "")
    history = state.get("chat_history", [])

    context = "\n".join([f"{m['role']}: {m['content']}" for m in history[-4:]])

    prompt = f"""
            You are helping a user complete a brief. The last answer seemed off.

            Rephrase the question in a more helpful and conversational way, based on this context.
            If you think more information is needed, add a clarifying follow-up.

            Original question: {question}

            Context:
            {context}

            Only return the new assistant message.
            """
    result = llm.invoke([HumanMessage(content=prompt)])
    content = result.content.strip()
    return re.sub(r"^(AI|Assistant|System):", "", content).strip()