import streamlit as st
from orchestrator.orchestrator import initialize_state, run_classification, run_brief, process_user_response_to_question

st.set_page_config(page_title="RFx AI Builder Assistant", layout="centered")
st.title("RFx AI Builder Assistant")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = initialize_state()

state = st.session_state.conversation_state

# Show chat history
for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).markdown(msg["content"], unsafe_allow_html=True)

# Sidebar upload + logs
log_placeholder = None
if state["step"] >= 2:
    with st.sidebar:
        st.markdown("## 📄 Document Upload (Optional)")
        uploaded_files = st.file_uploader(
            "Upload supporting RFx Documents (Brief, meeting minutes, etc)", 
            type=["pdf", "docx", "txt"], 
            accept_multiple_files=True
        )

        if uploaded_files:
            filenames_seen = set()
            state["uploaded_texts"] = []
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in filenames_seen:
                    filenames_seen.add(uploaded_file.name)
                    content = uploaded_file.read().decode("utf-8", errors="ignore")
                    state["uploaded_texts"].append({"name": uploaded_file.name, "content": content})
                    state["logs"].append(f"📄 Document '{uploaded_file.name}' uploaded.")

        st.markdown("## 🗞️ RFx Information")
        if state.get("rfx_type"):
            st.success(f"Request Type: {state['rfx_type']}")
        else:
            st.info("No classification yet")

        log_placeholder = st.empty()
        if state["logs"]:
            with log_placeholder:
                st.markdown("## 📚 View log steps")
                with st.expander("View log steps", expanded=True):
                    shown_logs = set()
                    for log in state["logs"]:
                        if log not in shown_logs:
                            if not any(tag in log for tag in ["[INFO]", "[STEP]", "[TIMING]"]):
                                st.markdown(f"- {log}")
                            shown_logs.add(log)

        if st.button("🔁 Reset Chat"):
            st.session_state.chat_history = []
            st.session_state.conversation_state = initialize_state()
            st.rerun()

# Step 0: Welcome
if state["step"] == 0:
    welcome = "Hi! I’m your RFx assistant. How can I help you today?"
    st.chat_message("assistant").write(welcome)
    st.session_state.chat_history.append({"role": "assistant", "content": welcome})
    state["step"] = 1

# Step 1: User input
if state["step"] == 1:
    user_input = st.chat_input("Please describe your RFx need (e.g. request details or document).")
    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        if user_input.strip().lower() in ["hi", "hello", "hey"]:
            msg = "Hi! Could you please describe what you're looking to build?"
        else:
            msg = "You can upload <span style='color:green'><b>supporting RFx Documents</b></span> in the sidebar."
            state["user_input"] = user_input
            state["step"] = 2
        st.chat_message("assistant").markdown(msg, unsafe_allow_html=True)
        st.session_state.chat_history.append({"role": "assistant", "content": msg})
        st.rerun()

# Step 2: Classification
if state["step"] == 2:
    if st.button("Start Building RFx"):
        with st.spinner("🔎 Classifying your request..."):
            rfx_type, full_label = run_classification(state)
        if f"✅ Classification complete: {rfx_type}" not in state["logs"]:
            state["logs"].append(f"✅ Classification complete: {rfx_type}")
        msg = f"This looks like a **{rfx_type} ({full_label})**. Do you want to proceed?"
        st.chat_message("assistant").write(msg)
        st.session_state.chat_history.append({"role": "assistant", "content": msg})
        state["step"] = 3

# Step 3: Confirm type
if state["step"] == 3:
    if state.get("rfx_type") and not state.get("type_confirmed"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, proceed"):
                state["type_confirmed"] = True
                st.chat_message("assistant").write(f"You confirmed the request type: {state['rfx_type']}")
                st.session_state.chat_history.append({"role": "assistant", "content": f"You confirmed the request type: {state['rfx_type']}"})

                with st.spinner("Extracting information from documents...") if state.get("uploaded_texts") else st.empty():
                    brief_data, missing_sections, disclaimer = run_brief(state)

                state["brief_data"] = brief_data
                state["missing_sections"] = missing_sections
                state["disclaimer"] = disclaimer

                if disclaimer:
                    state["disclaimer_shown"] = True
                    st.chat_message("assistant").write(disclaimer)
                    st.session_state.chat_history.append({"role": "assistant", "content": disclaimer})

                if missing_sections:
                    section, sub = missing_sections[0]
                    question = brief_data[section][sub]["question"]
                    state["pending_question"] = {"section": section, "sub": sub, "question": question}
                    st.chat_message("assistant").write(question)
                    st.session_state.chat_history.append({"role": "assistant", "content": question})

                state["step"] = 5
                st.rerun()

        with col2:
            if st.button("❌ No, change type"):
                state["step"] = 4

# Step 4: Manual selection
if state["step"] == 4 and not state.get("manual_selected"):
    st.chat_message("assistant").write("What type of RFx would you like to proceed with?")
    col1, col2, col3 = st.columns(3)
    selected = None
    if col1.button("📄 RFP"):
        selected = "RFP"
    elif col2.button("💰 RFQ"):
        selected = "RFQ"
    elif col3.button("📚 RFI"):
        selected = "RFI"

    if selected:
        state["rfx_type"] = selected
        state["manual_selected"] = True
        brief_data, missing_sections, disclaimer = run_brief(state)
        msg = f"You selected {selected}. {disclaimer}" if disclaimer else f"You selected {selected}."
        st.chat_message("assistant").write(msg)
        st.session_state.chat_history.append({"role": "assistant", "content": msg})
        state["brief_data"] = brief_data
        state["missing_sections"] = missing_sections
        state["disclaimer"] = disclaimer

        if disclaimer:
            state["disclaimer_shown"] = True
            st.chat_message("assistant").write(disclaimer)
            st.session_state.chat_history.append({"role": "assistant", "content": disclaimer})

        if missing_sections:
            section, sub = missing_sections[0]
            question = brief_data[section][sub]["question"]
            state["pending_question"] = {"section": section, "sub": sub, "question": question}
            st.chat_message("assistant").write(question)
            st.session_state.chat_history.append({"role": "assistant", "content": question})

        state["step"] = 5
        st.rerun()

# Step 5: Q&A if needed
if state.get("pending_question"):
    question = state["pending_question"]["question"]
    user_input = st.chat_input(question)

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("⏭️ Skip", key="skip_question"):
            response = process_user_response_to_question(state, "_")
            st.chat_message("assistant").write(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()

    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        response = process_user_response_to_question(state, user_input)
        st.chat_message("assistant").write(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

# Step 5: Generate final document
if state["step"] == 5 and not state.get("document_generated") and not state.get("pending_question"):
    if st.button("📄 Generate Final Document"):
        from orchestrator.orchestrator import generate_final_document
        with st.spinner("Generating Word document..."):
            file_path = generate_final_document(state)
            state["document_generated"] = True
            state["document_path"] = file_path
            msg = "The final document has been generated. You can download it below."
            st.chat_message("assistant").write(msg)
            st.session_state.chat_history.append({"role": "assistant", "content": msg})
            st.rerun()

if state["step"] == 5 and state.get("document_generated") and state.get("document_path"):
    st.success("🎉 Document generated!")
    with open(state["document_path"], "rb") as f:
        st.download_button(
            label="⬇️ Download Document",
            data=f,
            file_name="Generated_RFQ.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
