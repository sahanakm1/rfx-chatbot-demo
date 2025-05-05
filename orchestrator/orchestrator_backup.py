# orchestrator.py
from agents.brief_intake_agent import run_brief_intake, update_brief_with_user_response
from agents.classification_agent import classify_rfx
from agents.draft_generator import build_doc_from_json

RFX_TYPE_LABELS = {
    "RFP": "Request for Proposal",
    "RFQ": "Request for Quotation",
    "RFI": "Request for Information"
}

def initialize_state():
    return {
        "step": 0,
        "user_input": "",
        "rfx_type": None,
        "uploaded_texts": [],
        "output_message": "",
        "logs": [],
        "manual_selected": False,
        "brief": {},
        "pending_question": None,
        "missing_sections": [],
        "document_generated": False,
        "document_path": None
    }

def run_classification(state):
    logs = []

    def log_callback(msg):
        logs.append(msg)

    uploaded_texts = state.get("uploaded_texts", [])
    combined_text = "\n\n".join([doc["content"] for doc in uploaded_texts]) if uploaded_texts else ""

    result = classify_rfx(
        text=combined_text,
        user_input=state.get("user_input", ""),
        log_callback=log_callback
    )

    state["rfx_type"] = result.get("rfx_type")
    state["logs"] += logs + result.get("logs", [])
    return state["rfx_type"], RFX_TYPE_LABELS.get(state["rfx_type"], "")

def run_brief(state):
    state["logs"].append("📑 Scanning documents to extract RFx information...")
    brief_data, missing_sections = run_brief_intake(
        rfx_type=state.get("rfx_type"),
        user_input=state.get("user_input", ""),
        uploaded_texts=state.get("uploaded_texts", [])
    )

    state["brief"] = brief_data
    state["missing_sections"] = missing_sections

    if missing_sections:
        section, sub = missing_sections[0]
        state["pending_question"] = {
            "section": section,
            "sub": sub,
            "question": brief_data[section][sub]["question"]
        }
        return brief_data[section][sub]["question"]

    return "Initial brief generated successfully."

def process_user_response_to_question(state, user_response: str):
    pending = state.get("pending_question")
    if not pending:
        return "No pending question to process."

    section = pending["section"]
    sub = pending["sub"]
    state["brief"] = update_brief_with_user_response(state["brief"], section, sub, user_response)

    state["missing_sections"] = [s for s in state["missing_sections"] if s != (section, sub)]
    state["pending_question"] = None

    if state["missing_sections"]:
        section, sub = state["missing_sections"][0]
        question = state["brief"][section][sub]["question"]
        state["pending_question"] = {
            "section": section,
            "sub": sub,
            "question": question
        }
        return question

    return "Thank you. The brief is now complete."

def generate_final_document(state) -> str:
    brief = state.get("brief", {})
    formatted_data = {
        section: {
            sub: qa.get("answer", "(No content provided)")
            for sub, qa in subs.items()
        }
        for section, subs in brief.items()
    }
    return build_doc_from_json(formatted_data)