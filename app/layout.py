import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from ui_helpers import render_chat_history, render_download_button
from orchestrator.orchestrator import initialize_state, run_classification, run_brief, process_user_response_to_question, generate_final_document
from agents.brief_intake_agent import try_auto_answer
from state_handler import render_logs, handle_uploaded_files, is_vague_response, render_vague_response_options, render_step_5_input, log_event
from agents.chat_agent import handle_conversation, stream_conversation

def render_left_panel(state):
    with st.container():
        st.markdown("<p style='font-size:13px; font-weight:600;'>📄 Upload Documents</p>", unsafe_allow_html=True)
        with st.container():
            st.markdown("""
            <style>
                section[data-testid=\"stFileUploader\"] > div {
                    background-color: #ffffff;
                    border: 1px solid #ccc;
                    padding: 0.75rem;
                }
            </style>
            """, unsafe_allow_html=True)
            uploaded_files = st.file_uploader("Upload RFx files", type=["pdf", "docx", "txt"], accept_multiple_files=True)
            if uploaded_files:
                initial_count = len(state.get("uploaded_texts", []))
                handle_uploaded_files(state, uploaded_files)
                new_docs = state.get("uploaded_texts", [])[initial_count:]
                if new_docs:
                    names = ", ".join(doc["name"] for doc in new_docs)
                    state["chat_history"].append({
                        "role": "assistant",
                        "content": f"📎 Document(s) uploaded successfully: {names}"
                    })
                    st.rerun()

        st.markdown("<p style='font-size:13px; font-weight:600; margin-top: 1rem;'>🧾 Logs</p>", unsafe_allow_html=True)
        render_logs(state)

        st.markdown("""
        <style>
        div[data-testid=\"baseButton-secondary\"] button,
        div[data-testid=\"baseButton-primary\"] button {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #ccc;
        }
        </style>
        """, unsafe_allow_html=True)
        if st.button("🔁 Reset Chat", key="reset_chat_btn"):
            st.session_state.conversation_state = initialize_state()
            st.rerun()

def render_chat_history(state):
    for msg in state.get("chat_history", []):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        is_user = role == "user"
        avatar = "👤" if is_user else "🤖"

        align = "flex-end" if is_user else "flex-start"
        bg = "#f5f5f5" if is_user else "#f5f5f5"
        border = "#f5f5f5" if is_user else "#f5f5f5"
        text_color = "#000000"

        st.markdown(f"""
        <div style='
            display: flex;
            justify-content: {align};
            margin: 0.5rem 0;
        '>
            <div style='
                background-color: {bg};
                color: {text_color};
                border: 1px solid {border};
                border-radius: 10px;
                padding: 1rem;
                max-width: 80%;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            '>
                <div style='font-size: 0.9rem; margin-bottom: 0.25rem;'>
                    <b>{avatar}</b>
                </div>
                <div style='font-size: 1rem; line-height: 1.5;'>{content}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_center_panel(state):
    st.markdown("""
        <style>
        .chat-wrapper {
            display: flex;
            flex-direction: column;
            
        }

        .scrollable-chat {
            flex: 1;
            overflow-y: auto;
            padding-right: 1rem;
            padding-bottom: 1rem;
            display: flex;
            flex-direction: column;
        }

        .fixed-input {
            padding-top: 1rem;
            padding-bottom: 1rem;
            border-top: 1px solid #ccc;
            background-color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    if "chat_history" not in state:
        state["chat_history"] = []

    if state["step"] == 0:
        welcome = "Hi! I’m your RFx assistant. How can I help you today?"
        state["chat_history"].append({"role": "assistant", "content": welcome})
        state["step"] = 1
        st.rerun()

    with st.container():
        st.markdown("<div class='chat-wrapper'>", unsafe_allow_html=True)

        st.markdown("<div class='scrollable-chat'>", unsafe_allow_html=True)
        render_chat_history(state)

        if state["step"] == 1 and state.get("pending_response"):
            user_input = state.pop("pending_response")
            streamed_text = ""
            with st.container():
                animated_placeholder = st.empty()
                animation_frames = [".", "..", "..."]
                for _ in range(6):
                    for frame in animation_frames:
                        animated_placeholder.markdown(f"<div><b>🤖 Assistant is writing{frame}</b></div>", unsafe_allow_html=True)
                        time.sleep(0.2)
                animated_placeholder.empty()

                placeholder = st.empty()
                for chunk in stream_conversation(state, user_input):
                    streamed_text += chunk
                    placeholder.markdown(f"<div style='margin-top: 0.5rem;'><b>🤖 Assistant:</b> {streamed_text}</div>", unsafe_allow_html=True)

            state["chat_history"].append({"role": "assistant", "content": streamed_text})
            if state.get("uploaded_texts") or state.get("intent") == "create":
                state["user_input"] = user_input
                state["step"] = 2
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)  # close scrollable-chat

        st.markdown("<div class='fixed-input'>", unsafe_allow_html=True)
        
        user_input = st.chat_input("Please describe your RFx need or upload a document to begin.")
        if user_input:
            if state.get("step") == 5 and state.get("pending_question"):
                if is_vague_response(user_input):
                    render_vague_response_options(state, user_input)
                    return
                state["chat_history"].append({"role": "user", "content": user_input})
                response = process_user_response_to_question(state, user_input)
                state["chat_history"].append({"role": "assistant", "content": response})
                del state["pending_question"]
                state.pop("question_displayed", None)
                st.rerun()
            else:
                state["chat_history"].append({"role": "user", "content": user_input})
                state["pending_response"] = user_input
                st.rerun()


        st.markdown("</div>", unsafe_allow_html=True)  # close fixed-input

        st.markdown("</div>", unsafe_allow_html=True)  # close chat-wrapper

    if state["step"] == 2 and st.button("Start Building RFx", key="start_building"):
        if not state.get("uploaded_texts"):
            log_event(state, "[Info] No User document is uploaded")
        log_event(state, "[AGENT] Classification agent started")
        state["trigger_classification"] = True
        st.rerun()
    
    if state["step"] == 2 and state.get("trigger_classification"):
        with st.spinner("🔎 Classifying your request..."):
            rfx_type, full_label = run_classification(state)
        state["rfx_type"] = rfx_type
        log_event(state, f"[Status] Classification complete: {rfx_type}")
        state["step"] = 3
        del state["trigger_classification"]
        msg = f"This looks like a **{rfx_type} ({full_label})**. Do you want to proceed?"
        state["chat_history"].append({"role": "assistant", "content": msg})
        st.rerun()

    if state["step"] == 3:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, proceed", key="confirm_type"):
                state["type_confirmed"] = True
                log_event(state, "[AGENT] Brief Intake agent started. LLM Content generation & Missing details Q&A in progress")
                with st.spinner("Running Brief Intake Agent..."):
                    brief_data, missing_sections, disclaimer = run_brief(state)
                state.update({
                    "brief_data": brief_data,
                    "missing_sections": missing_sections,
                    "disclaimer": disclaimer,
                    "step": 5
                })
                st.rerun()
        with col2:
            if st.button("❌ No, change type", key="change_type"):
                state["step"] = 4

    if state["step"] == 4:
        st.markdown("<p style='font-size:14px; font-weight:500;'>Select RFx type manually</p>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        if col1.button("📄 RFP"):
            state["rfx_type"] = "RFP"
        elif col2.button("💰 RFQ"):
            state["rfx_type"] = "RFQ"
        elif col3.button("📚 RFI"):
            state["rfx_type"] = "RFI"
        if state.get("rfx_type"):
            brief_data, missing_sections, disclaimer = run_brief(state)
            state.update({
                "brief_data": brief_data,
                "missing_sections": missing_sections,
                "disclaimer": disclaimer,
                "step": 5
            })
            st.rerun()
    
    if state["step"] == 5 and state.get("pending_question"):
        question = state["pending_question"]["question"]
        state["chat_history"].append({"role": "assistant", "content": question})
        answer = try_auto_answer(state)
        if answer == "N/A":
            render_step_5_input(state, question)
        else:
            state["chat_history"].append({"role": "assistant", "content": answer})
            response = process_user_response_to_question(state, answer)
            state["chat_history"].append({"role": "assistant", "content": response})
            st.rerun()

    if state["step"] == 5 and not state.get("pending_question") and not state.get("document_generated"):
        if st.button("📄 Generate Final RFx Brief", key="generate_doc"):
            log_event(state, "[[AGENT] Draft generator agent started")
            with st.spinner("Generating final document..."):
                file_path = generate_final_document(state)
                state.update({
                    "document_generated": True,
                    "document_path": file_path
                })
                log_event(state, "[Status] Final brief available for download")
                msg = "The final document has been generated. You can download it from the right panel."
                state["chat_history"].append({"role": "assistant", "content": msg})
                st.rerun()

def render_right_panel(state):
    with st.container():
        st.markdown("<p style='font-size:14px; font-weight:600;'>📑 Generated Content</p>", unsafe_allow_html=True)
        if state.get("brief_data"):
            for section, subs in state["brief_data"].items():
                with st.expander(section):
                    for subsec, content in subs.items():
                        st.markdown(f"**{subsec}**")
                        st.markdown(content.get("answer", "_No content yet._"))
        elif not state.get("document_generated"):
            st.markdown("<i>No sections generated yet.</i>", unsafe_allow_html=True)

        if state.get("document_generated") and state.get("document_path"):
            render_download_button(state["document_path"])

    st.markdown("<hr style='border-top: 1px solid #ccc;'>", unsafe_allow_html=True)