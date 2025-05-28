# state_handler.py
# Refactored: removed Streamlit dependencies for WebSocket backend

import uuid
import os
from docx import Document
import pdfplumber

from agents.document_ingestor import ingest_document
from agents.document_reader import read_file_as_documents

def initialize_state():
    return {
        "step": 0,
        "logs": [],
        "chat_history": [],
        "uploaded_texts": [],
        "rfx_type": None,
        "trigger_classification": False,
        "type_confirmed": False,
        "manual_selected": False,
        "brief_data": {},
        "section_content": {},
        "missing_sections": [],
        "pending_question": None,
        "pending_refine_request": None,
        "disclaimer": None,
        "disclaimer_shown": False,
        "document_generated": False,
        "document_path": None,
        "show_left_panel": True,
        "show_right_panel": True,
        "displayed_generate_msg": False,
        "displayed_ready_msg": False,
        "displayed_appendix_hint": False,
        "collection_name": f"rfx_session_{uuid.uuid4().hex[:8]}"
    }

def log_event(state, message):
    state["logs"].append(message)


def handle_uploaded_files(state, uploaded_files):
    if "uploaded_texts" not in state:
        state["uploaded_texts"] = []

    filenames_seen = {doc["name"] for doc in state["uploaded_texts"]}

    for uploaded_file in uploaded_files:
        if uploaded_file.name in filenames_seen:
            continue

        if state.get("appendix_mode", False):
            existing = {f.name for f in state.get("appendix_files", [])}
            if uploaded_file.name not in existing:
                state.setdefault("appendix_files", []).append(uploaded_file)
            log_event(state, f"[Info] Appendix document '{uploaded_file.name}' uploaded (no ingestion)")
            continue
        else:
            try:
                documents, content = read_file_as_documents(uploaded_file, uploaded_file.name)
                collection = state.get("collection_name", "rfx_default")
                ingest_document(
                    documents=documents,
                    doc_id_prefix=uploaded_file.name,
                    collection_name=collection
                )
                state["uploaded_texts"].append({
                    "name": uploaded_file.name,
                    "content": content
                })
            except Exception as e:
                print(f"[Warning] Could not process {uploaded_file.name}: {e}")

        log_msg = f"[Info] User document '{uploaded_file.name}' uploaded"
        if log_msg not in state["logs"]:
            log_event(state, log_msg)
            if state.get("pending_question"):
                state["pending_question"]["asked"] = False
                state["next_action"] = "ask_brief_question"
                log_event(state, "[Action] trigger pending question with new document")
            else:
                state["next_action"] = "trigger_after_upload"
            state["langgraph_ran"] = False
