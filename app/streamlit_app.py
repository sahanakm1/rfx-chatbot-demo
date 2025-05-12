import streamlit as st
from ui_helpers import render_chat_history, render_download_button
from state_handler import initialize_state, render_logs
from layout import render_left_panel, render_center_panel, render_right_panel
from langchain_ollama import OllamaLLM

st.set_page_config(page_title="RFx AI Builder Assistant", layout="wide")

def warm_up_llm():
    try:
        llm = OllamaLLM(model="mistral")
        llm.invoke(["Just say hi."])  # short dummy request to preload model
    except Exception as e:
        print("LLM warm-up failed:", e)

warm_up_llm()  # ✅ Pre-warms LLM before user types anything

# Initialize session state
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = initialize_state()
state = st.session_state.conversation_state

# Safe-guard keys
state.setdefault("chat_history", [])
state.setdefault("logs", [])

# Title + styling
st.markdown("<h1 style='text-align: center;'>RFx AI Builder Assistant</h1><hr>", unsafe_allow_html=True)

# Panels: wider center, fixed width sides
col_left, col_center, col_right = st.columns([1, 2.8, 1], gap="large")

with col_left:
    render_left_panel(state)

with col_center:
    render_center_panel(state)

with col_right:
    render_right_panel(state)