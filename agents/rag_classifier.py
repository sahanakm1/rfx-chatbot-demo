from agents.llm_calling import llm_calling
import time

PROMPT_PATH = "prompts/classification_prompt.txt"

def normalize_rfx_type(value: str) -> str:
    val = value.strip().lower()
    if "rfp" in val or "proposal" in val:
        return "RFP"
    elif "rfq" in val or "quotation" in val or "quote" in val:
        return "RFQ"
    elif "rfi" in val or "information" in val:
        return "RFI"
    return "Unknown"

PROMPT_PATH = "prompts/classification_prompt.txt"

def classify_with_rag(vector_db, chat_context: str = "", model_name: str = "mistral") -> str:
    with open(PROMPT_PATH) as f:
        system_prompt = f.read()

    llm = llm_calling(model_name=model_name).call_llm()

    retrieved_docs = vector_db.similarity_search("What type of RFx is this document?")
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"User input: {chat_context}\n\nContent:\n{context}"}
    ]

    start = time.time()
    response = llm.invoke(messages)
    print(f"[TIMING] RAG classification took {time.time() - start:.2f}s")

    result = normalize_rfx_type(response.content)
    return result