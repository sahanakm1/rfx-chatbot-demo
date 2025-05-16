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



def refine_user_answer(state):
    """Improves the user's answer by adding clarity, structure, or missing context."""
    llm = llm_calling().call_llm()

    pending = state.get("pending_question", {})
    question = pending.get("question", "")
    answer = state.get("user_input", "")
    history = state.get("chat_history", [])
    uploaded_texts = state.get("uploaded_texts", [])

    # Tomar últimos 4 intercambios del chat
    chat_context = "\n".join([f"{m['role']}: {m['content']}" for m in history[-4:]])

    # Incluir contenido del documento si lo hay
    doc_context = ""
    if uploaded_texts:
        doc_context = uploaded_texts[0].get("content", "")[:3000]  # Limita longitud para evitar overflow

    prompt = f"""
                        You are assisting a user to complete a professional brief for an RFx response.

                        Your task is to improve or refine the user's answer to a question by:
                        - Adding relevant context if missing
                        - Rephrasing for clarity and tone
                        - Making sure it matches the purpose of the question

                        Use the following inputs:

                        🔹 Original question:
                        {question}

                        🔹 User's answer:
                        {answer}

                        🔹 Chat history:
                        {chat_context}

                        🔹 Extract from reference document:
                        {doc_context}

                        Please rewrite the user's answer in a way that is more complete, polished, and aligned with the brief’s purpose. 
                        Only output the refined answer, no explanation.
                        """

    result = llm.invoke([HumanMessage(content=prompt)])
    return re.sub(r"^(AI|Assistant|System):", "", result.content.strip()).strip()