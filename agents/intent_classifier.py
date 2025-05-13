from agents.llm_calling import llm_calling
import time

PROMPT_PATH = "prompts/classification_prompt.txt"

# Normalize output to standard RFx types
def normalize_rfx_type(value: str) -> str:
    val = value.strip().lower()
    if "rfp" in val or "proposal" in val:
        return "RFP"
    elif "rfq" in val or "quotation" in val or "quote" in val or "price" in val:
        return "RFQ"
    elif "rfi" in val or "information" in val or "learn" in val:
        return "RFI"
    return "Unknown"

# Classify RFx intent using only the user's input (no RAG or documents)
def classify_by_intent(user_input: str, model_name: str = "mistral") -> str:
    # Load system prompt for classification
    with open(PROMPT_PATH) as f:
        system_prompt = f.read()

    # Ignore simple greetings
    if user_input.strip().lower() in ["hi", "hello", "hey"]:
        return "Unknown"

    # Initialize LLM
    llm = llm_calling(model_name=model_name).call_llm()

    # Construct LLM input message
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    # Run inference and measure time
    start = time.time()
    response = llm.invoke(messages)
    print(f"[TIMING] Intent classification took {(time.time() - start)/60:.2f} min")

    # Normalize output
    result = normalize_rfx_type(response.content)
    return result
