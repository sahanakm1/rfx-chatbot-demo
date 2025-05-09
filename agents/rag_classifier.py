from agents.llm_calling import llm_calling
import time

PROMPT_PATH = "prompts/classification_prompt.txt"

def normalize_rfx_type(value: str) -> str:
    val = value.strip().lower()
    if "rfp" in val or "proposal" in val:
        return "RFP"
    elif "rfq" in val or "quotation" in val or "quote" in val or "price" in val:
        return "RFQ"
    elif "rfi" in val or "information" in val or "learn" in val:
        return "RFI"
    return "Unknown"

PROMPT_PATH = "prompts/classification_prompt.txt"

def classify_with_rag(vector_db, chat_context: str = "", model_name: str = "mistral") -> str:
    with open(PROMPT_PATH) as f:
        system_prompt = f.read()

    llm = llm_calling(model_name=model_name).call_llm()

    # Retrieve top 5 relevant chunks from the document
    retrieved_docs = vector_db.similarity_search("What type of RFx is this document?", k=5)
    context = "\n\n".join(doc.page_content.strip() for doc in retrieved_docs if doc.page_content.strip())

    """
    # Debug: print the chunks being used
    print("\n[DEBUG] Top retrieved chunks:")
    for i, doc in enumerate(retrieved_docs):
        print(f"[Chunk {i+1}] {doc.page_content[:300]}...\n")
    """

    # Construct prompt: exclude chat_context when doc is available
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{context}"}
    ]

    # LLM prediction
    start = time.time()
    response = llm.invoke(messages)
    print(f"[TIMING] RAG classification took {(time.time() - start)/60:.2f} min")
    
    result = normalize_rfx_type(response.content)
    return result