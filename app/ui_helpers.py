# ui_helpers.py
# Contains utility functions for consistent UI rendering across the app: background styling,
# chat message display, and file download functionality.

import streamlit as st
import os

def set_background():
    # Apply global styling to Streamlit app to match white, minimalistic theme
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

def render_chat_history(state):
    # Render all messages in the chat history with styling and avatar indicators
    for msg in state.get("chat_history", []):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        is_user = role == "user"
        avatar = "👤" if is_user else "🤖"

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
    # Render a download button for the generated RFx document if file exists
    if not filepath or not os.path.exists(filepath):
        return

    with open(filepath, "rb") as f:
        st.download_button(
            label="⬇️ Download RFx Brief",
            data=f,
            file_name="Generated_RFx_document.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )