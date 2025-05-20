# agents/chat_agent.py

#from langchain_ollama import OllamaLLM
#MODEL_NAME = "mistral"  # Use 'mistral' model if acceptable performance
# Initialize LLM
#llm = OllamaLLM(model=MODEL_NAME)

from agents.llm_calling import llm_calling
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import re

MAX_HISTORY = 4         # Number of previous messages to include in context

# Calling Gpt model
llm = llm_calling().call_llm()

# Load the initial system prompt for the assistant
def load_system_prompt():
    with open("prompts/initial_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()

# Heuristics to detect vague user inputs
def is_vague_input(text):
    text = text.lower().strip()
    vague_phrases = ["not sure", "idk", "don't know", "just exploring", "explore", "no idea", "need help"]
    return any(p in text for p in vague_phrases)

# Handle full conversation flow (used in non-streaming context)
def handle_conversation(state, user_input):
    # Set user's intent based on the input
    if is_vague_input(user_input):
        state["intent"] = "vague"
    elif "document" in user_input.lower():
        state["intent"] = "has_document"
    elif any(word in user_input.lower() for word in ["pricing", "proposal", "quote", "quotation", "request", "vendor", "build", "create"]):
        state["intent"] = "create"

    # ✅ Exit early if intent is clear
    if state.get("rfx_type") or state.get("intent") == "create":
        return "Got it. Let me know if you'd like help building your RFx or uploading supporting details."

    history = state.get("chat_history", [])
    messages = [SystemMessage(content=load_system_prompt())]

    # Only include the last few exchanges to reduce token load
    recent_history = history[-MAX_HISTORY:]
    for msg in recent_history:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))

    # Append current user input
    messages.append(HumanMessage(content=user_input))

    # Generate model response
    raw_response = llm.invoke(messages)
    content = raw_response.content if hasattr(raw_response, "content") else raw_response
    if content is None:
        content = ""

    cleaned_response = re.sub(r"^(AI|Assistant|System):\s*", "", content).strip()

    return cleaned_response


# Streaming version of the conversation
def stream_conversation(state, user_input):
    if is_vague_input(user_input):
        state["intent"] = "vague"
    elif "document" in user_input.lower():
        state["intent"] = "has_document"
    elif any(word in user_input.lower() for word in ["pricing", "proposal", "quote", "quotation", "request", "vendor", "build", "create"]):
        state["intent"] = "create"

    history = state.get("chat_history", [])
    messages = [SystemMessage(content=load_system_prompt())]

    recent_history = history[-MAX_HISTORY:]
    for msg in recent_history:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=user_input))

    # Return a generator that streams the model's response
    return llm.stream(messages)

# Generate a generic question if a brief section is missing
def generate_question_for_section(section_key) -> str:
    print(section_key)
    return f"Could you please provide more details about '{section_key}'?"

# Add a friendly note about detected RFx type to the assistant's message
def append_rfx_comment(state, context):
    rfx_type = state.get("rfx_type", "unspecified")
    prompt = f"""
                You are an assistant helping a business user from the procurement department respond to RFx requests.

                The user hasn't explicitly asked about the RFx type, but you (the assistant) have carefully analyzed the available information — including their written input and any uploaded documents — using the `Classification Agent`.

                The RFx has been automatically classified as: **{rfx_type}**.

                Your goal is to write a short and professional message in **Markdown format**. The message should be clear, business-friendly, and easy to read. Avoid any technical jargon.

                📌 Your message must include:

                1. A clear explanation that the user's input was reviewed by the `Classification Agent`.
                2. A confirmation of the **detected RFx type** (e.g., **RFP**, **RFI**, **RFQ**).
                3. A call to action: the user can now begin drafting the document based on that classification.
                4. An optional path: they may also manually adjust the RFx type if needed.
                5. A final sentence asking politely for confirmation to proceed.

                ✅ Format guidance:
                - Use **bold** to highlight the RFx type and key agent references.
                - The response should be suitable for a business user in procurement or operations.
                - Write in a concise, respectful, and supportive tone.
                - The entire message should be in **Markdown**.
                - Please avoid saying Hello or Thanks to the user.

                ---
                Previous assistant message (for reference):  
                {context}
                """



    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, "content") else str(response)
    return re.sub(r"^(AI|Assistant|System):\s*", "", content).strip()
    #return re.sub(r"^(AI|Assistant|System):\s*", "", response).strip()


# Generate a reformulated question for a given brief section and sub-question
def generate_question_for_section(state, original_question):
    prompt = f"""
                You are assisting a user in completing a **Request for {state.get("rfx_type")}** brief as part of a professional procurement process.

                Your task is to write the **next question** in a way that feels like a natural continuation of the flow — as if you're smoothly guiding the user through the next section of the document.

                Please:
                - Use a **professional and business-friendly tone**, suitable for procurement teams.
                - Ensure the question is **clear, concise, and easy to respond to**.
                - The message must be **readable in markdown**.
                - Use **bold** to emphasize key terms or important actions.
                - Do **not** say that you are rephrasing a question — the user should feel they are being guided seamlessly through the brief.
                - You may start with a sentence like “Let’s continue with the next section…” or “Now, moving on to…” if it fits naturally.

                ---

                **Original question:**  
                "{original_question}"

                Please return only the improved question in markdown format.
                """

    response = llm.invoke([HumanMessage(content=prompt)])
    return re.sub(r"^(AI|Assistant|System):\s*", "", str(response.content)).strip()

def should_trigger_classification(state):

    print("🔍 should_trigger_classification called")
    recent_inputs = [m["content"] for m in state.get("chat_history", []) if m["role"] == "user"]
    if not recent_inputs:
        return False

    chat_history = "\n".join(
        f"{msg['role']}: {msg['content']}" for msg in state["chat_history"]
    )

    with open("prompts/classification_readiness_prompt.txt", encoding="utf-8") as f:
        prompt = f.read().replace("{chat_history}", chat_history)

    llm = llm_calling().call_llm()
    response = llm.invoke([{"role": "user", "content": prompt}])

    # 🔍 Log to terminal
    #print("📜 LLM Prompt:\n", prompt)
    print("🤖 Should Classify LLM Response:", response.content.strip())

    return response.content.strip().upper() == "YES"
