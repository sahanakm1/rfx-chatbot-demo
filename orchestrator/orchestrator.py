from agents.brief_intake_agent import run_brief_intake, update_brief_with_user_response
from agents.chat_agent import generate_question_for_section
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
        "rfx_confirmed": False,
        "brief_ran": False,
        "document_generated": False,
        "doc_name": "Generated_Document",
        "document_path": ""
    }

import time

def run_classification(state):
    logs = []

    def log_callback(msg):
        logs.append(msg)

    uploaded_texts = state.get("uploaded_texts", [])
    combined_text = "\n\n".join([doc["content"] for doc in uploaded_texts]) if uploaded_texts else ""

    start_time = time.time()

    result = classify_rfx(
        text=combined_text,
        user_input=state.get("user_input", ""),
        log_callback=log_callback
    )

    duration = round((time.time() - start_time) / 60, 2)
    print(f"[TIMING] RAG classification took {duration} min")

    state["rfx_type"] = result.get("rfx_type")

    # Print detailed logs to terminal only
    for log in logs + result.get("logs", []):
        print(log)

    return state["rfx_type"], RFX_TYPE_LABELS.get(state["rfx_type"], "")


def run_brief(state):
    def dual_logger(msg):
        print(msg)  # Log to console (for dev visibility)
        
    brief_data, missing_sections, disclaimer_msg = run_brief_intake(
        rfx_type=state.get("rfx_type"),
        user_input=state.get("user_input", ""),
        uploaded_texts=state.get("uploaded_texts", []),
        log_callback=dual_logger,
        doc_name=state.get("doc_name","name")
    )

    state["brief"] = brief_data
    state["missing_sections"] = missing_sections
    state["disclaimer"] = disclaimer_msg

    if missing_sections:
        section, sub = missing_sections[0]
        question = generate_question_for_section(brief_data[section][sub])
        state["pending_question"] = {
            "section": section,
            "sub": sub,
            "question": question
        }

    return brief_data, missing_sections, disclaimer_msg


def process_user_response_to_question(state, user_response: str):
    pending = state.get("pending_question")
    if not pending:
        return "No pending question to process."

    section = pending["section"]
    sub = pending["sub"]
    response = update_brief_with_user_response(state, user_response)

    state["missing_sections"] = [s for s in state["missing_sections"] if s != (section, sub)]
    state["pending_question"] = None

    if state["missing_sections"]:
        section, sub = state["missing_sections"][0]
        question = generate_question_for_section(state["brief"][section][sub])
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
        section_key: {
            sub_key: qa.get("answer", "(No content provided)")
            for sub_key, qa in sub_dict.items()
        }
        for section_key, sub_dict in brief.items()
    }
    return build_doc_from_json(formatted_data)