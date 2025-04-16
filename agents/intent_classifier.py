from agents.llm_calling import llm_calling

def classify_by_intent(user_input: str, model_name: str = "llama3") -> str:
    """
    Classify the RFx intent based on user input only (no document).
    """
    llm = llm_calling(model_name=model_name).call_llm()

    system_prompt = (
        "You are an intelligent assistant helping users determine what kind of RFx they want to create.\n"
        "Based on the user's message, decide whether their intent is a Request for Proposal (RFP),\n"
        "Request for Quotation (RFQ), or Request for Information (RFI).\n"
        "Respond with only one of these values: RFP, RFQ, RFI, or Unknown."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    response = llm.invoke(messages)
    result = response.content.strip().upper()
    return result if result in ["RFP", "RFQ", "RFI"] else "Unknown"