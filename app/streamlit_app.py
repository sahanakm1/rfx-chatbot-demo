# streamlit_app.py
# Entry point for the RFx AI Builder Assistant. Sets up Streamlit layout, state, and LangGraph execution.

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from layout import render_left_panel, render_center_panel, render_right_panel
from state_handler import initialize_state
from orchestrator.main_graph import build_graph

# Set Streamlit app configuration
st.set_page_config(page_title="RFx AI Builder Assistant", layout="wide")

# Initialize conversation state if not already set
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = initialize_state()

state = st.session_state.conversation_state

# Build LangGraph only once per session
if "langgraph" not in st.session_state:
    st.session_state.langgraph = build_graph()

graph = st.session_state.langgraph

# Run LangGraph agent if any user interaction is pending
if not state.get("langgraph_ran") and (
    state.get("user_input") or
    state.get("pending_question") or
    state.get("uploaded_texts") or
    state.get("next_action") or
    state.get("intent")):
    with st.spinner("🧠 Thinking..."):
        updated_state = graph.invoke(state)
        updated_state["langgraph_ran"] = True
        st.session_state.conversation_state = updated_state
        state = updated_state

        # 👇 Segunda invocación si el router dejó una acción pendiente
        if updated_state.get("next_action"):
            second_state = graph.invoke(updated_state)
            second_state["langgraph_ran"] = True
            st.session_state.conversation_state = second_state
            state = second_state

# Render the UI layout (three panels)
st.markdown("<h1 style='text-align: center;'>RFx AI Builder Assistant</h1><hr>", unsafe_allow_html=True)

col_left, col_center, col_right = st.columns([1, 2.8, 1], gap="large")

with col_left:
    render_left_panel(state)

with col_center:
    render_center_panel(state)

with col_right:
    render_right_panel(state)
