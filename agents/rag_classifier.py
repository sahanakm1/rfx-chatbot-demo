from agents.llm_calling import llm_calling

def classify_with_rag(vector_db, chat_context: str = "") -> str:
    """
    Classify RFx type using retrieved content and LLaMA3 LLM.
    """
    llm = llm_calling().call_llm()
    retrieved_docs = vector_db.similarity_search("What type of RFx is this document?")
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    system_prompt = (
        "You are an AI assistant that classifies RFx documents based on retrieved content.\n"
        "Decide if the content reflects a Request for Proposal (RFP),\n"
        "Request for Quotation (RFQ), or Request for Information (RFI).\n"
        "Respond with only: RFP, RFQ, RFI, or Unknown."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"User input: {chat_context}\n\nContent:\n{context}"}
    ]

    response = llm.invoke(messages)
    result = response.content.strip().upper()
    return result if result in ["RFP", "RFQ", "RFI"] else "Unknown"