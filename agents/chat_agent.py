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
            You are an assistant helping a user respond to RFx requests.
            The user hasn't asked directly about the RFx type, but you (the assistant) know it has been classified as: {rfx_type}.

            Generate a short, helpful sentence to naturally inform the user of this classification.
            Make it sound helpful and conversational. For example:
            - "By the way, this seems to be an RFI."
            - "It looks like you're dealing with an RFP. Want help drafting it?"
            ---

            Previous message from assistant (if any): 
            {context}
            """

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, "content") else str(response)
    return re.sub(r"^(AI|Assistant|System):\s*", "", content).strip()
    #return re.sub(r"^(AI|Assistant|System):\s*", "", response).strip()


# Generate a reformulated question for a given brief section and sub-question
def generate_question_for_section(state, original_question):
    prompt = f"""
                You are helping a user complete a Request for {state.get("rfx_type")} brieft.

                Rephrase the following question in a friendly, conversational, and helpful tone. Make sure it’s clear and easy to answer:

                Original question: "{original_question}"

                Avoid being too technical. Keep it short, natural, and specific.
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
    print("🤖 SouldClassify LLM Response:", response.content.strip())

    return response.content.strip().upper() == "YES"
