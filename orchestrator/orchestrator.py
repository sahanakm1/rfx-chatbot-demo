from agents.brief_intake_agent import run_brief_intake, update_brief_with_user_response
from agents.chat_agent import generate_question_for_section
from agents.classification_agent import classify_rfx
from agents.draft_generator import build_doc_from_json
from agents.document_ingestor import ingest_document
import uuid
import time

# Etiquetas legibles para tipos de RFx
RFX_TYPE_LABELS = {
    "RFP": "Request for Proposal",
    "RFQ": "Request for Quotation",
    "RFI": "Request for Information"
}

# Inicializa el estado con una colección única para esta sesión
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
        "document_path": "",
        "collection_name": f"rfx_session_{uuid.uuid4().hex[:8]}"
    }


def ingest_uploaded_documents(state, model_name: str = "mistral"):
    collection_name = state.get("collection_name", "rfx_default")

    for doc in state.get("uploaded_texts", []):
        doc_name = doc.get("name")
        content = doc.get("content", "")

        if not content.strip():
            state["logs"].append(f"[Warning] Document '{doc_name}' is empty, skipping.")
            continue

        try:
            ingest_document(doc_id=doc_name, text=content, model_name=model_name, collection_name=collection_name)
            state["logs"].append(f"[Info] Document '{doc_name}' vectorized into collection '{collection_name}'.")
        except Exception as e:
            state["logs"].append(f"[Error] Failed to ingest '{doc_name}': {e}")



def run_classification(state, model_name: str = "mistral"):
    from agents.classification_agent import classify_rfx

    logs = []
    user_input = state.get("user_input", "").strip()
    collection_name = state.get("collection_name", "")
    uploaded_texts = state.get("uploaded_texts", [])

    def log_callback(msg):
        logs.append(msg)

    result = classify_rfx(
        user_input=user_input,
        collection_name=collection_name,
        model_name=model_name,
        uploaded_texts=uploaded_texts,
        log_callback=log_callback
    )

    rfx_type = result.get("rfx_type", "Unknown")
    state["rfx_type"] = rfx_type

    for log in logs + result.get("logs", []):
        print(log)

    return rfx_type, RFX_TYPE_LABELS.get(rfx_type, "")



def run_brief(state):
    """
    Ejecuta el agente de generación de brief.
    """
    def dual_logger(msg):
        print(msg)

    brief_data, missing_sections, disclaimer_msg = run_brief_intake(
        rfx_type=state.get("rfx_type"),
        user_input=state.get("user_input", ""),
        uploaded_texts=state.get("uploaded_texts", []),
        log_callback=dual_logger,
        doc_name=state.get("doc_name", "name"),
        collection_name=state.get("collection_name","")
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
    """
    Procesa la respuesta del usuario a una pregunta pendiente en el brief.
    """
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
    """
    Genera el documento Word a partir del brief final.
    """
    brief = state.get("brief", {})
    formatted_data = {
        section_key: {
            sub_key: qa.get("answer", "(No content provided)")
            for sub_key, qa in sub_dict.items()
        }
        for section_key, sub_dict in brief.items()
    }
    return build_doc_from_json(formatted_data)