# orchestrator/orchestrator.py

from agents.brief_intake_agent import run_brief_intake, generate_section_from_retrieval, update_brief_with_user_response
from agents.classification_agent import classify_rfx
from agents.draft_generator import build_doc_from_json
from agents.chat_agent import generate_question_for_section
from agents.brief_intake_agent import update_brief_with_user_response
from creating_retriever import universal_retrieval, user_retriever
from agents.llm_calling import llm_calling
from pathlib import Path
from langgraph.types import Command, interrupt
from pprint import pprint

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
        "uploaded_text": None,
        "output_message": "",
        "logs": [],
        "manual_selected": False,
        "un_retriever": None,
        "us_retriever": None,
        "brief": {},
        "pending_question": None,
        "missing_sections": [],
        "document_generated": False,
        "document_path": "",
        "app": None,
        "thread": None,
    }

def load_universal_retrieval(type_of_retrieval="dense"):
    embeddings = llm_calling(embedding_model="llama3").call_embed_model()
    collection_name = "jti_rfp_dense"
    path = "./tmp/langchain_qdrant_dense"
    db_path = Path(f"{path}/collection/{collection_name}/storage.sqlite")

    if db_path.is_file():
        return universal_retrieval(
            embeddings=embeddings,
            collection_name=collection_name,
            path=path
        ).load_existing_vdb_collection()
    else:
        raise FileNotFoundError("Universal vectorstore not found. Run create_universal_vectorstore.py first.")

def load_user_retrieval(file_name, content, type_of_retrieval="dense"):
    embeddings = llm_calling(embedding_model="llama3").call_embed_model()
    collection_name = file_name
    path = f"./tmp/langchain_qdrant_user_{type_of_retrieval}"
    db_path = Path(f"{path}/collection/{collection_name}/storage.sqlite")

    if db_path.is_file():
        return universal_retrieval(
            embeddings=embeddings,
            collection_name=collection_name,
            path=path
        ).load_existing_vdb_collection()
    else:
        return user_retriever(
            collection_name=collection_name,
            embeddings=embeddings,
            path=path,
            doc_input=content,
            type_of_retrieval=type_of_retrieval
        ).create_new_vdb()

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
        rfx_type=state.get("rfx_type"),
        user_input=state.get("user_input", ""),
        uploaded_text=state.get("uploaded_text", ""),
        retriever_input=state.get("un_retriever"),
        retriever_user=state.get("us_retriever")
    )

    state["brief"] = brief_data
    state["missing_sections"] = missing_sections

    if missing_sections:
        next_section = missing_sections[0]
        question = next_section
        state["pending_question"] = {
            "section": next_section,
            "question": question
        }
        return f"I need more information about **{next_section}**: {question}"

    return "Initial brief has been generated successfully."

def process_user_response_to_question(state, user_response: str):
    pending = state.get("pending_question")
    if not pending:
        return "No pending question to process."

    section = pending["question"]
    state["brief"] = update_brief_with_user_response(state["brief"], section, user_response)
    state["pending_question"] = None

    return "Thank you. The brief is now updated."

def generate_without_interrupt(inputs, thread, app):
    for output in app.stream(inputs, thread):
        for key, value in output.items():
            pprint(f"Node '{key}':")
    return key, value

def generate_with_interrupt(user_input, thread, app):
    for output in app.stream(Command(resume=user_input), thread, stream_mode="updates"):
        for key, value in output.items():
            pprint(f"Node '{key}':")
    return value

def generate_final_document(state) -> str:
    brief = state.get("brief", {})
    file_path = build_doc_from_json(brief)
    return file_path
