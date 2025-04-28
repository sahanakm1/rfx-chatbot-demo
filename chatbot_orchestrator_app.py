# chatbot_app.py
import streamlit as st
from orchestrator.orchestrator import initialize_state, run_classification,run_brief, process_user_response_to_question


st.set_page_config(page_title="RFx AI Builder Assistant", layout="centered")
st.title("RFx AI Builder Assistant")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = initialize_state()

state = st.session_state.conversation_state

# Show chat history
for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["content"])

def display_logs(logs, log_placeholder):
    if logs and log_placeholder:
        with log_placeholder:
            st.markdown("## 📚 Processing Log")
            with st.expander("View log steps", expanded=True):
                for log in logs:
                    st.markdown(f"- {log}")

# Sidebar
log_placeholder = None
if state["step"] >= 2:
    with st.sidebar:
        st.markdown("## 📄 Document Upload (Optional)")
        uploaded_file = st.file_uploader("Upload a supporting RFx Document", type=["pdf", "docx", "txt"])
        if uploaded_file:
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            state["uploaded_text"] = content
            doc_msg = f"Document '{uploaded_file.name}' uploaded."
            if doc_msg not in state["logs"]:
                state["logs"].append(doc_msg)

        st.markdown("## 🧾 RFx Information")
        if state.get("rfx_type"):
            st.success(f"Detected Type: {state['rfx_type']}")
        else:
            st.info("No classification yet")

        log_placeholder = st.empty()
        if state["logs"]:
            with log_placeholder:
                st.markdown("## 📚 Processing Log")
                with st.expander("View log steps", expanded=True):
                    for log in state["logs"]:
                        st.markdown(f"- {log}")

        if st.button("🔁 Reset Chat"):
            st.session_state.chat_history = []
            st.session_state.conversation_state = initialize_state()
            st.rerun()



# Step 0: Greet
if state["step"] == 0:
    welcome = "Hi! I’m your RFx assistant. How can I help you today?"
    st.chat_message("assistant").write(welcome)
    st.session_state.chat_history.append({"role": "assistant", "content": welcome})
    state["step"] = 1

# Step 1: Wait for user input
if state["step"] == 1:
    user_input = st.chat_input("Please describe your RFx need (e.g. request details or document).")
    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        state["user_input"] = user_input
        state["step"] = 2
        st.rerun()

# Step 2: Classification
if state["step"] == 2:
    if st.button("Start Building RFx"):
        with st.spinner("🔎 Classifying your request..."):
            rfx_type, full_label = run_classification(state)
            display_logs(state["logs"], log_placeholder)

        msg = f"This looks like a **{rfx_type} ({full_label})**. Do you want to proceed?"
        st.chat_message("assistant").write(msg)
        st.session_state.chat_history.append({"role": "assistant", "content": msg})
        state["step"] = 3

# Step 3: Confirm type
if state["step"] == 3:
    if state.get("rfx_type"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, proceed"):
                msg = run_brief(state)
                st.chat_message("assistant").write(msg)
                st.session_state.chat_history.append({"role": "assistant", "content": msg})
                state["step"] = 5
        with col2:
            if st.button("❌ No, change type"):
                state["step"] = 4

# Step 4: Manual selection
if state["step"] == 4 and not state.get("manual_selected"):
    st.chat_message("assistant").write("What type of RFx would you like to proceed with?")
    col1, col2, col3 = st.columns(3)
    selected = None
    if col1.button("📄 Request for Proposal"):
        selected = "RFP"
    elif col2.button("💰 Request for Quotation"):
        selected = "RFQ"
    elif col3.button("📚 Request for Information"):
        selected = "RFI"

    if selected:
        state["rfx_type"] = selected
        state["manual_selected"] = True
        msg = run_brief(state)
        st.chat_message("assistant").write(f"You selected {selected}. {msg}")
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"User selected {selected}. {msg}"
        })
        state["step"] = 5
        st.rerun()



# Show pending question if exists
if state.get("pending_question"):
    question = state["pending_question"]["question"]
    user_input = st.chat_input(question)
    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        response = process_user_response_to_question(state, user_input)
        st.chat_message("assistant").write(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()


# Step 5: Generate and download final document
if state["step"] == 5 and not state.get("document_generated"):
    
    if st.button("📄 Generate Final Document"):
        with st.spinner("Generating Word document..."):
            from orchestrator.orchestrator import generate_final_document
            file_path = generate_final_document(state)
            state["document_generated"] = True
            state["document_path"] = file_path

            msg = "The final document has been generated. You can download it below."
            st.chat_message("assistant").write(msg)
            st.session_state.chat_history.append({"role": "assistant", "content": msg})
            st.rerun()


# Step 5 (continued): Show download link if document exists
if  state["step"] == 5 and state.get("document_generated") and state.get("document_path"):
    st.success("🎉 Document generated!")
    with open(state["document_path"], "rb") as f:
        st.download_button(
            label="⬇️ Download Generated Document",
            data=f,
            file_name="Generated_RFQ.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )