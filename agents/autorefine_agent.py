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
            You are assisting a user in completing an RFx brief for a procurement process.

            The user's last answer was flagged as problematic by the `Consistency Checker Agent`  — it was considered **irrelevant**, **incomplete**, or **not aligned** with the original question.

            As a result, the `Refinement Agent` has been activated to rephrase or enhance the question so the user can provide a better response.

            Your goal:

            1. Begin with a short, professional sentence explaining that both `Consistency Checker Agent` and  `Refinement Agent` reviewed the last input. Let the user know the previous answer didn't fully match the expected information, and you're here to help clarify the request.  
                 ➤ This introduction should appear in a separate paragraph.
            2. Reformulate the original question using business-appropriate language, typical of procurement or vendor evaluation scenarios.
            3. Optionally, include a follow-up clarification to guide the user if the question could be ambiguous.
            4. Ensure the response is readable in **Markdown** format, using **bold** to highlight key terms. Do not extra use of the bold format, be clean please.
            5. Keep the tone professional, respectful, and helpful — tailored for a procurement team or business stakeholder.
            6. Please try to be consice and clear.

            ---

            📌 **Original question:**  
            {question}

            📄 **Brief context (if helpful):**  
            {context}

            ---

            Please return only the improved message in Markdown format — starting with the intro and followed by the reformulated question.
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