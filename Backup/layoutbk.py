# layout.py
# This file contains Streamlit UI layout logic divided into three panels: left (uploads + logs),
# center (chat interface), and right (debug + brief output). It manages user interaction states visually.

import sys
import os
import time
import markdown
import streamlit as st
from ui_helpers import render_chat_history, render_download_button_for_zip, render_download_button_for_docx
from state_handler import render_logs, handle_uploaded_files, is_vague_response, render_vague_response_options, log_event
from prompts.brief_structure import SECTION_TITLES

def inject_layout_styles():
    st.markdown("""
        <style>
        .rfx-header {
            font-size: 19px;
            font-weight: 1200;
            margin-bottom: 0.4rem;
            color: #000000 !important;
        }
        </style>
    """, unsafe_allow_html=True)


def render_left_panel(state):
    # Upload documents panel
    with st.container():
        st.markdown("<p class='rfx-header'>📄 Upload supporting documents</p>", unsafe_allow_html=True)
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

            # Allow more types when uploading appendices
            is_appendix = state.get("document_generated", False)
            state["appendix_mode"] = is_appendix

            allowed_types = (
                ["pdf", "docx", "txt", "xlsx", "csv", "png", "jpg", "jpeg", "ppt", "pptx"]
                if is_appendix else
                ["pdf", "docx", "txt"]
            )

            uploaded_files = st.file_uploader(
                "Upload RFx or supporting files",
                type=allowed_types,
                accept_multiple_files=True
            )

            if uploaded_files:
                from state_handler import handle_uploaded_files

                # Determine if brief already exists → treat uploads as appendix
                is_appendix = state.get("document_generated", False)
                state["appendix_mode"] = is_appendix

                # Avoid duplicates
                already_uploaded = {f["name"] for f in state.get("uploaded_texts", [])}
                already_appendices = {f.name for f in state.get("appendix_files", [])}
                deduplicated_files = [
                    f for f in uploaded_files
                    if f.name not in already_uploaded and f.name not in already_appendices
                ]

                if deduplicated_files:
                    handle_uploaded_files(state, deduplicated_files)
                    state["appendix_mode"] = False

                    file_names = ", ".join(f.name for f in deduplicated_files)

                    # Add to chat history
                    if is_appendix:
                        state.setdefault("appendix_files", []).extend(deduplicated_files)
                        state["chat_history"].append({
                            "role": "assistant",
                            "content": f"📎 Uploaded appendix files: {file_names}"
                        })
                        st.success(f"{len(deduplicated_files)} appendix file(s) uploaded.")

                        # ✅ Immediately regenerate final ZIP
                        state["next_action"] = "draft_generator"
                        state["langgraph_ran"] = False
                        st.rerun()

                        # # ✅ Flag for draft regeneration (but rerun in next cycle)
                        # state["trigger_regeneration"] = True

                    else:
                        state["chat_history"].append({
                            "role": "assistant",
                            "content": f"📎 Document(s) uploaded successfully: {file_names}"
                        })

                        # If there is a pending question, retry it with the new document
                        if state.get("pending_question"):
                            # update unanswerable_sections so the RAG model can try again the actual and following sections
                            missing_set = set(state.get("missing_sections", []))
                            state["unanswerable_sections"] = [
                                pair for pair in state.get("unanswerable_sections", [])
                                if pair not in missing_set
                            ]

                            # Reintentar la pregunta actual
                            state["pending_question"]["asked"] = False
                            state["next_action"] = "ask_brief_question"
                            log_event(state, "[Action] layout - trigger pending question with new document")
                        else:
                            state["next_action"] = "trigger_after_upload"

                        state["langgraph_ran"] = False
                        st.rerun()
                else:
                    st.info("All selected files have been uploaded.")

        # Display logs
        st.markdown("<p class='rfx-header'>🧾 Logs</p>", unsafe_allow_html=True)
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
    for msg in state.get("chat_history", []):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        content = markdown.markdown(content)

        is_user = role == "user"

        align = "flex-end" if is_user else "flex-start"
        bg_color = "#e0f0ff" if is_user else "#f8f8f8"
        avatar = "🙎" if is_user else "🤖"
        text_color = "#000"
        border = "#d3d3d3"

        st.markdown(f"""
        <div style="display: flex; justify-content: {align}; margin: 0.5rem 0;">
            <div style="
                max-width: 70%;
                padding: 1rem;
                background-color: {bg_color};
                border: 1px solid {border};
                border-radius: 12px;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
                font-family: 'Segoe UI', sans-serif;
                font-size: 15px;
                color: {text_color};
            ">
                <div style="margin-bottom: 0.5rem;"><b>{avatar}</b></div>
                <div>{content}</div>
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

    # If conversation hasn't started, welcome the user
    if not state.get("conversation_started"):
        welcome = f"""**Hi there! I’m your RFx AI Assistant.**  
                        Whether you're starting from scratch or already have documents prepared, I'm here to support you. You can:  
                        <br>
                        &nbsp;&nbsp;&nbsp;- **Upload any RFx-related files** (e.g., draft documents, notes, past briefs), or  
                        &nbsp;&nbsp;&nbsp;- **Describe what you're working on**, and I'll guide you step-by-step through building your RFx brief.  
                        <br>
                        Behind the scenes, I rely on a team of specialized AI agents - each focused on understanding, classifying, and helping you structure the content.  
                        Just let me know how you'd like to begin."""
        state["chat_history"].append({"role": "assistant", "content": welcome})
        state["conversation_started"] = True
        st.rerun()

    with st.container():
        st.markdown("<div class='chat-wrapper'>", unsafe_allow_html=True)
        st.markdown("<div class='scrollable-chat'>", unsafe_allow_html=True)

        # Render previous messages
        render_chat_history(state)

        # Handle any pending_response from earlier UI
        if state.get("pending_response"):
            user_input = state.pop("pending_response")
            state["chat_history"].append({"role": "user", "content": user_input})
            state["user_input"] = user_input
            state["langgraph_ran"] = False
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)  # scrollable-chat
        st.markdown("<div class='fixed-input'>", unsafe_allow_html=True)

        # Chat input
        user_input = st.chat_input("Please describe your RFx need or upload a document to begin.")
        if user_input:
            # Always append to history immediately
            state["chat_history"].append({"role": "user", "content": user_input})
            state["user_input"] = user_input
            state["langgraph_ran"] = False
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)  # fixed-input
        st.markdown("</div>", unsafe_allow_html=True)  # chat-wrapper

def render_right_panel(state):
    # Debug and output panel
    with st.container():
        if state.pop("brief_updated", False):
            st.rerun()

        st.markdown("<p class='rfx-header'>📁 Brief Data</p>", unsafe_allow_html=True)
        #st.json(state.get("brief", {}))

        st.markdown("<p style='font-size:14px; font-weight:600;'>Generated Contents for review</p>", unsafe_allow_html=True)
        if state.get("brief"):
             for section, subs in state["brief"].items():
                section_title = SECTION_TITLES.get(section, section)
                with st.expander(section_title):
                    for subsec, content in subs.items():
                        answer = content.get("answer", "").strip()
                        title = content.get("title", subsec)  # fallback to A.1 if title is missing
                        st.markdown(f"**{title}**")
                        if answer and answer.upper() != "N/A":
                            st.markdown(answer)
                        else:
                            st.markdown("_No content yet._")

        elif not state.get("document_generated"):
            st.markdown("<i>No sections generated yet.</i>", unsafe_allow_html=True)


        # ✅ Show download buttons if doc is ready
        if state.get("document_generated"):
            st.markdown("<p class='rfx-header'>📥 Click here to download the RFx documents</p>", unsafe_allow_html=True)
            if state.get("docx_path"):
                render_download_button_for_docx(state["docx_path"])

            # 📦 Show ZIP button if available
            if state.get("zip_path") and os.path.exists(state["zip_path"]):
                with open(state["zip_path"], "rb") as f:
                    st.download_button(
                        label="📦 Download Full RFx Package (ZIP)",
                        data=f,
                        file_name="Final_RFx_Package.zip",
                        mime="application/zip"
                    )

                # 🧾 Optional: list appendix file names below ZIP
                appendix_files = state.get("appendix_files", [])
                if appendix_files:
                    st.markdown("<p style='font-size:13px; margin-top:1rem;'>📎 Files added to ZIP:</p>", unsafe_allow_html=True)
                    
                    seen_files = set()
                    for file in appendix_files:
                        if file.name not in seen_files:
                            st.markdown(f"- {file.name}")
                            seen_files.add(file.name)

                    # for file in appendix_files:
                    #     #st.markdown(f"- {file['name']}")
                    #     st.markdown(f"- {file.name}")

    st.markdown("<hr style='border-top: 1px solid #ccc;'>", unsafe_allow_html=True)