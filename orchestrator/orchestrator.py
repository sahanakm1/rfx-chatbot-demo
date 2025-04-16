import streamlit as st
from orchestrator.orchestrator import Orchestrator

# Page setup
st.set_page_config(page_title="RFx AI Builder Assistant", layout="centered")
st.title("RFx AI Builder Assistant")

# Load system prompt
with open("prompts/initial_prompt.txt") as f:
    system_prompt = f.read()

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "step" not in st.session_state:
    st.session_state.step = 0
if "rfx_type" not in st.session_state:
    st.session_state.rfx_type = None
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()

# Show chat history
for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["content"])

# Step 0: Greeting only
if st.session_state.step == 0:
    st.chat_message("assistant").write("Hi! I’m your RFx assistant. How can I help you today?")
    st.session_state.chat_history.append({"role": "assistant", "content": "Hi! I’m your RFx assistant. How can I help you today?"})
    st.session_state.step = 1

# Step 1: Wait for user input
if st.session_state.step == 1:
    user_input = st.chat_input("Describe what you need help with...")
    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.step = 2
        st.session_state.chat_context = user_input

# Step 2: Ask for document or scratch
if st.session_state.step == 2:
    st.chat_message("assistant").write("Would you like to upload an existing RFx document or create one from scratch?")
    choice = st.radio("Choose one:", ["Upload Document", "Start from Scratch"])
    if choice == "Upload Document":
        uploaded_file = st.file_uploader("Upload RFx Document", type=["pdf", "docx", "txt"])
        if uploaded_file and uploaded_file != st.session_state.uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            st.chat_message("assistant").write(f"Thanks for uploading '{uploaded_file.name}'. Sending it for classification...")
            st.session_state.chat_history.append({"role": "assistant", "content": f"Document '{uploaded_file.name}' uploaded."})

            # Read and classify using orchestrator
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            rfx_type = st.session_state.orchestrator.handle_document_upload(content, st.session_state.get("chat_context", ""))
            st.chat_message("assistant").write(f"This appears to be a {rfx_type}.")
            st.session_state.chat_history.append({"role": "assistant", "content": f"Classified as: {rfx_type}"})
            st.session_state.rfx_type = rfx_type
            st.session_state.step = 3
    elif choice == "Start from Scratch":
        st.chat_message("assistant").write("Great! Let me guide you through creating your RFx from scratch.")
        st.session_state.chat_history.append({"role": "assistant", "content": "User chose to start from scratch."})

        # Ask orchestrator to classify based on user input
        user_input = st.session_state.get("chat_context", "")
        rfx_type = st.session_state.orchestrator.handle_chat_intent(user_input)
        st.chat_message("assistant").write(f"Thanks! Based on our conversation, this seems to be a {rfx_type}.")
        st.session_state.chat_history.append({"role": "assistant", "content": f"Classified as: {rfx_type}"})
        st.session_state.rfx_type = rfx_type
        st.session_state.step = 3

# Step 3 — Placeholder for continuing logic
if st.session_state.step == 3:
    st.chat_message("assistant").write("Next, I will gather details about your request... (To be implemented)")