# state_handler.py
# Handles application-wide state logic, including initialization, chat history, document tracking,
# logging, vague input handling, and section rendering logic.

import uuid
import streamlit as st
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

def set_background():
    style = """
    <style>
    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: #ffffff;
        color: #000000;
        font-family: 'Segoe UI', sans-serif;
    }
    .chat-line {
        margin: 0.75rem 0;
        font-size: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #f0f0f0;
    }
    .chat-line.user {
        text-align: left;
        font-weight: bold;
    }
    .chat-line.assistant {
        text-align: left;
    }
    [data-testid="stSidebar"] > div:first-child {
        border-right: 2px solid #ccc;
    }
    .block-container {
        display: flex;
        gap: 2rem;
    }
    [data-testid="column"] {
        border-left: 2px solid #ccc;
        padding-left: 1rem;
    }
    footer, header, .st-emotion-cache-zq5wmm {
        visibility: hidden;
        height: 0;
    }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

def render_logs(state):
    if not state.get("logs"):
        return

    if "highlight_log_index" not in st.session_state:
        st.session_state.highlight_log_index = len(state["logs"]) - 1

    with st.expander("📚 View log steps", expanded=True):
        for idx, log in enumerate(state["logs"]):
            if idx == st.session_state.highlight_log_index:
                st.markdown(
                    f"<div style='background-color:lightgrey;padding:6px;border-radius:6px;color:#000000'>{log}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(f"- {log}")

def log_event(state, message):
    state["logs"].append(message)
    st.session_state.highlight_log_index = len(state["logs"]) - 1

def render_chat_history(state):
    for msg in state.get("chat_history", []):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        is_user = role == "user"
        avatar = "🙎" if is_user else "🤖"

        align = "flex-end" if is_user else "flex-start"
        bg = "#dcf8c6" if is_user else "#f8f9fa"
        border = "#cccccc" if is_user else "#e0e0e0"

        st.markdown(f"""
        <div style='display: flex; justify-content: {align}; margin: 0.5rem 0;'>
            <div style='background-color: {bg}; border: 1px solid {border}; border-radius: 10px; padding: 1rem; max-width: 80%; box-shadow: 0 2px 5px rgba(0,0,0,0.05);'>
                <div style='font-size: 0.9rem; margin-bottom: 0.25rem;'><b>{avatar}</b></div>
                <div style='font-size: 1rem; line-height: 1.5;'>{content}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_download_button(filepath):
    if not filepath or not os.path.exists(filepath):
        return
    with open(filepath, "rb") as f:
        st.download_button(
            label="⬇️ Download RFx Brief",
            data=f,
            file_name="Generated_RFx_document.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

def render_section_content(state):
    if not state.get("section_content"):
        st.markdown("_No sections generated yet._")
        return

    visible_sections = {
        k: v for k, v in state["section_content"].items()
        if v.get("text") and v.get("text").strip().lower() != "n/a"
    }

    if not visible_sections:
        st.markdown("_No sections generated yet._")
        return

    st.markdown("### 📑 Generated Sections")
    for section_title, section_data in visible_sections.items():
        status = section_data.get("status", "ready")
        tag = "✅" if status == "ready" else "🕒"
        with st.expander(f"{tag} {section_title}", expanded=False):
            st.markdown(section_data["text"])
            if st.button(f"⏭️ Skip '{section_title}'", key=f"skip_{section_title}"):
                state["logs"].append(f"[User] Skipped section: {section_title}")
                st.rerun()

    if state.get("document_generated") and state.get("document_path"):
        render_download_button(state["document_path"])

def is_vague_response(user_input):
    vague_keywords = ["idk", "not sure", "n/a", "tbd", "don't know", "no idea"]
    return any(kw in user_input.lower() for kw in vague_keywords)

def render_vague_response_options(state, user_input):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✍️ Help me write it"):
            state["chat_history"].append({"role": "user", "content": user_input})
            state["pending_refine_request"] = "auto-draft"
            st.rerun()
    with col2:
        if st.button("⏭️ Skip this section"):
            state["pending_refine_request"] = "skip"
            st.rerun()

def extract_docx_text(uploaded_file):
    doc = Document(uploaded_file)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])

def handle_uploaded_files(state, uploaded_files):
    if "uploaded_texts" not in state:
        state["uploaded_texts"] = []

    filenames_seen = {doc["name"] for doc in state["uploaded_texts"]}

    for uploaded_file in uploaded_files:
        if uploaded_file.name in filenames_seen:
            continue

        

        
        if state.get("appendix_mode", False):
            # If uploading as appendix only — do NOT ingest
            existing = {f.name for f in state.get("appendix_files", [])}
            if uploaded_file.name not in existing:
                state.setdefault("appendix_files", []).append(uploaded_file)
            log_event(state, f"[Info] Appendix document '{uploaded_file.name}' uploaded (no ingestion)")
            continue
        else:
            # Otherwise, process for classification
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

            # triger again the question after upload
            if state.get("pending_question"):
                state["pending_question"]["asked"] = False
                state["next_action"] = "ask_brief_question"
                log_event(state, "[Action] state_handler -trigger pending question with new document")
            else:
                state["next_action"] = "trigger_after_upload"

            state["langgraph_ran"] = False