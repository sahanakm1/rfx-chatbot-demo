from agents.llm_calling import llm_calling
import time

PROMPT_PATH = "prompts/classification_prompt.txt"

# Normalize model response into a standard RFx category
def normalize_rfx_type(value: str) -> str:
    val = value.strip().lower()
    if "rfp" in val or "proposal" in val:
        return "RFP"
    elif "rfq" in val or "quotation" in val or "quote" in val or "price" in val:
        return "RFQ"
    elif "rfi" in val or "information" in val or "learn" in val:
        return "RFI"
    return "Unknown"

# Classify an RFx document using RAG (LLM + vector DB retrieval)
def classify_with_rag(vector_db, chat_context: str = "") -> str:
    # Load classification prompt
    with open(PROMPT_PATH) as f:
        system_prompt = f.read()

    # Initialize LLM
    #llm = llm_calling(model_name=model_name).call_llm()
    llm = llm_calling().call_llm()

    # Retrieve top 5 most relevant chunks from the document
    retrieved_docs = vector_db.similarity_search("What type of RFx is this document?", k=5)
    context = "\n\n".join(doc.page_content.strip() for doc in retrieved_docs if doc.page_content.strip())

    # Construct the LLM prompt without chat context if document chunks are present
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{context}"}
    ]

    # LLM inference
    start = time.time()
    response = llm.invoke(messages)
    print(f"[TIMING] RAG classification took {(time.time() - start)/60:.2f} min")

    # Normalize the model's output to one of the accepted RFx types
    result = normalize_rfx_type(response.content)
    return result
