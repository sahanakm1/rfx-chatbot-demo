# layout.py
# This file contains Streamlit UI layout logic divided into three panels: left (uploads + logs),
# center (chat interface), and right (debug + brief output). It manages user interaction states visually.

import sys
import os
import time
import streamlit as st
from ui_helpers import render_chat_history, render_download_button
from state_handler import render_logs, handle_uploaded_files, is_vague_response, render_vague_response_options, log_event

def render_left_panel(state):
    # Upload documents panel
    with st.container():
        st.markdown("<p style='font-size:13px; font-weight:600;'>📄 Upload Documents</p>", unsafe_allow_html=True)
        with st.container():
            # Style customization for file uploader
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
                # Track and log new document uploads
                initial_count = len(state.get("uploaded_texts", []))
                handle_uploaded_files(state, uploaded_files)
                new_docs = state.get("uploaded_texts", [])[initial_count:]
                if new_docs:
                    names = ", ".join(doc["name"] for doc in new_docs)
                    state["chat_history"].append({
                        "role": "assistant",
                        "content": f"📎 Document(s) uploaded successfully: {names}"
                    })
                    state["langgraph_ran"] = False
                    st.rerun()

        # Display logs
        st.markdown("<p style='font-size:13px; font-weight:600; margin-top: 1rem;'>🧾 Logs</p>", unsafe_allow_html=True)
        render_logs(state)

        # Style reset buttons
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
        # Reset conversation
        if st.button("🔁 Reset Chat", key="reset_chat_btn"):
            from state_handler import initialize_state
            st.session_state.conversation_state = initialize_state()
            st.rerun()

def render_chat_history(state):
    # Display conversation history
    for msg in state.get("chat_history", []):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        is_user = role == "user"
        avatar = "👤" if is_user else "🤖"
        align = "flex-end" if is_user else "flex-start"
        bg = "#f5f5f5"
        border = "#f5f5f5"
        text_color = "#000000"

        st.markdown(f"""
        <div style='display: flex; justify-content: {align}; margin: 0.5rem 0;'>
            <div style='background-color: {bg}; color: {text_color}; border: 1px solid {border}; border-radius: 10px; padding: 1rem; max-width: 80%; box-shadow: 0 2px 5px rgba(0,0,0,0.05);'>
                <div style='font-size: 0.9rem; margin-bottom: 0.25rem;'><b>{avatar}</b></div>
                <div style='font-size: 1rem; line-height: 1.5;'>{content}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_center_panel(state):
    # Main chat interface: message history + user input
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

    if not state.get("conversation_started"):
        welcome = "Hi! I’m your RFx assistant. How can I help you today?"
        state["chat_history"].append({"role": "assistant", "content": welcome})
        state["conversation_started"] = True
        st.rerun()

    with st.container():
        st.markdown("<div class='chat-wrapper'>", unsafe_allow_html=True)
        st.markdown("<div class='scrollable-chat'>", unsafe_allow_html=True)
        print("\n📜 Chat history before rendering:")
        for msg in state.get("chat_history", []):
            print("-", msg)
        render_chat_history(state)

        # Handle pending user input
        if state.get("pending_response"):
            user_input = state.pop("pending_response")
            state["user_input"] = user_input
            state["langgraph_ran"] = False
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='fixed-input'>", unsafe_allow_html=True)

        user_input = st.chat_input("Please describe your RFx need or upload a document to begin.")
        if user_input:
            if state.get("pending_question"):
                if is_vague_response(user_input):
                    render_vague_response_options(state, user_input)
                    return
                state["chat_history"].append({"role": "user", "content": user_input})
                state["user_input"] = user_input
                state["langgraph_ran"] = False
                st.rerun()
            else:
                state["chat_history"].append({"role": "user", "content": user_input})
                state["pending_response"] = user_input
                state["langgraph_ran"] = False
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)  # fixed-input
        st.markdown("</div>", unsafe_allow_html=True)  # chat-wrapper

def render_right_panel(state):
    # Debug and output panel
    with st.container():
        if state.pop("brief_updated", False):
            st.rerun()

        st.markdown("### Debug Brief Data")
        st.json(state.get("brief_data", {}))

        st.markdown("<p style='font-size:14px; font-weight:600;'>📁 Generated Content</p>", unsafe_allow_html=True)
        if state.get("brief_data"):
            for section, subs in state["brief_data"].items():
                with st.expander(section):
                    for subsec, content in subs.items():
                        answer = content.get("answer", "").strip()
                        st.markdown(f"**{subsec}**")
                        if answer and answer.upper() != "N/A":
                            st.markdown(answer)
                        else:
                            st.markdown("_No content yet._")
        elif not state.get("document_generated"):
            st.markdown("<i>No sections generated yet.</i>", unsafe_allow_html=True)

        if state.get("document_generated") and state.get("document_path"):
            render_download_button(state["document_path"])

    st.markdown("<hr style='border-top: 1px solid #ccc;'>", unsafe_allow_html=True)
