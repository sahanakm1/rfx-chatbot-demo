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


def classify_by_intent(user_input: str, model_name: str = "mistral") -> str:
    with open(PROMPT_PATH) as f:
        system_prompt = f.read()

    if user_input.strip().lower() in ["hi", "Hi", "Hello", "hello", "hey"]:
        return "Unknown"

    llm = llm_calling(model_name=model_name).call_llm()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    start = time.time()
    response = llm.invoke(messages)
    print(f"[TIMING] Intent classification took {(time.time() - start)/60:.2f} min")


    result = normalize_rfx_type(response.content)
    return result