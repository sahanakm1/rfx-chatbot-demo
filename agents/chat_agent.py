# agents/chat_agent.py

from langchain_ollama import OllamaLLM
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import re

MODEL_NAME = "mistral"  # Use 'mistral' when performance is acceptable
MAX_HISTORY = 4           # Limit how many past messages are sent to the LLM

# Load model
llm = OllamaLLM(model=MODEL_NAME)

# Load prompt from file
def load_system_prompt():
    with open("prompts/initial_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()

def is_vague_input(text):
    text = text.lower().strip()
    vague_phrases = ["not sure", "idk", "don't know", "just exploring", "explore", "no idea", "need help"]
    return any(p in text for p in vague_phrases)

def handle_conversation(state, user_input):
    # Intent detection
    if is_vague_input(user_input):
        state["intent"] = "vague"
    elif "document" in user_input.lower():
        state["intent"] = "has_document"
    elif any(word in user_input.lower() for word in ["pricing", "proposal", "quote", "quotation", "request", "vendor", "build", "create"]):
        state["intent"] = "create"

    history = state.get("chat_history", [])
    messages = [SystemMessage(content=load_system_prompt())]

    # Use only recent messages to keep LLM fast
    recent_history = history[-MAX_HISTORY:]
    for msg in recent_history:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))

    # Add current user message
    messages.append(HumanMessage(content=user_input))

    raw_response = llm.invoke(messages)
    cleaned_response = re.sub(r"^(AI|Assistant|System):\s*", "", raw_response).strip()

    # Generate assistant reply
    return cleaned_response

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

    return llm.stream(messages)  # returns a generator


def generate_question_for_section(section_key) -> str:
    questions = {
        "context": "Could you describe the background or context of this request?",
        "goals": "What are the primary objectives you're aiming to achieve?",
        "deliverables": "What specific outputs or deliverables are expected?",
        "dates": "What are the important dates or deadlines to consider?"
    }

    if isinstance(section_key, str):
        return questions.get(section_key.lower(), f"Could you please provide more details about '{section_key}'?")
    else:
        return "Could you please clarify which section you're referring to?"
