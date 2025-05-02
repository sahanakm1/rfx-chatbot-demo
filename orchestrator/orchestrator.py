# orchestrator.py

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
        "uploaded_text": "",
        "output_message": "",
        "logs": [],
        "manual_selected": False,
        "brief": {},
        "pending_question": None,
        "missing_sections": []
    }

def run_classification(state):
    logs = []

    def log_callback(msg):
        logs.append(msg)

    result = classify_rfx(
        text=state.get("uploaded_text", ""),
        user_input=state.get("user_input", ""),
        log_callback=log_callback
    )

    state["rfx_type"] = result.get("rfx_type")
    state["logs"] = logs + result.get("logs", [])
    return state["rfx_type"], RFX_TYPE_LABELS.get(state["rfx_type"], "")




def run_brief(state):
    brief_data, missing_sections = run_brief_intake(
        state.get("rfx_type"),
        state.get("user_input", ""),
        state.get("uploaded_text", "")
    )

    state["brief"] = brief_data
    state["missing_sections"] = missing_sections

    print(missing_sections)

    if missing_sections:
        section, sub = missing_sections[0]
        question = generate_question_for_section(brief_data[section][sub])
        state["pending_question"] = {
            "section": section,
            "sub": sub,
            "question": question
        }
        return f"{question}"

    return "Initial brief has been generated successfully."

def process_user_response_to_question(state, user_response: str):
    """
    Stores the user's answer to a pending question and updates the brief.
    Then checks if more sections are missing and prepares the next question.
    """
    print(state)
    print(user_response)

    pending = state.get("pending_question")
    if not pending:
        return "No pending question to process."

    section = pending["section"]
    sub = pending["sub"]
    state["brief"] = update_brief_with_user_response(state["brief"], section, sub, user_response)
    
    # Remove the answered section from the missing list
    state["missing_sections"] = [s for s in state["missing_sections"] if s != (section, sub)]
    state["pending_question"] = None

    if state["missing_sections"]:
        section, sub = state["missing_sections"][0]
        print("------1")
        print(section, sub)

        print("------1")
        print(state)

        # TODO: here must go the answer from the model to the next section
        #
        #

        # if the model do nos has an answer then generate question to the user  TODO: the following must go in a condition 
        question = generate_question_for_section(state["brief"][section][sub])
        state["pending_question"] = {
            "section": section,
            "sub": sub,
            "question": question
        }
        #return f"Thanks! Now, about **{next_section}**: {question}"
        return f"{question}"

    return "Thank you. The brief is now complete."

def generate_final_document(state) -> str:
    brief = state.get("brief", {})
    file_path = build_doc_from_json(brief)
    return file_path
