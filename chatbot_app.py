import streamlit as st
from agents.rfx_graph import rfx_graph

# Page setup
st.set_page_config(page_title="RFx AI Builder Assistant", layout="centered")
st.title("RFx AI Builder Assistant")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = {
        "step": 0,
        "user_input": "",
        "rfx_type": None,
        "uploaded_text": "",
        "output_message": ""
    }

# Display chat historygit checkout -b feature/chat-agent-enhancement

for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["content"])

# Step 0: Show greeting
if st.session_state.conversation_state["step"] == 0:
    welcome = "Hi! I’m your RFx assistant. How can I help you today?"
    st.chat_message("assistant").write(welcome)
    st.session_state.chat_history.append({"role": "assistant", "content": welcome})
    st.session_state.conversation_state["step"] = 1

# Step 1: Wait for user input and build input state
if st.session_state.conversation_state["step"] == 1:
    user_input = st.chat_input("Describe what you need help with...")
    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.conversation_state["user_input"] = user_input
        st.session_state.conversation_state["step"] = 2

# Step 2: Upload document (optional) and trigger LangGraph
if st.session_state.conversation_state["step"] == 2:
    uploaded_file = st.file_uploader("Upload an RFx Document (optional)", type=["pdf", "docx", "txt"])
    if uploaded_file is not None:
        content = uploaded_file.read().decode("utf-8", errors="ignore")
        st.session_state.conversation_state["uploaded_text"] = content

    if st.button("Start Building RFx"):
        state = st.session_state.conversation_state
        result = rfx_graph.invoke(state)
        response = result.get("output_message", "Something went wrong.")
        st.chat_message("assistant").write(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.session_state.conversation_state.update(result)