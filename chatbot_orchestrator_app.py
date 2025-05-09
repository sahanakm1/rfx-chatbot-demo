import streamlit as st
import pdfplumber
from orchestrator.orchestrator import initialize_state, run_classification, run_brief, process_user_response_to_question
from agents.brief_intake_agent import try_auto_answer
import base64

st.set_page_config(page_title="RFx AI Builder Assistant", layout="centered")

# --- Background image injection ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = f"""
    <style>
    html, body, [data-testid="stAppViewContainer"], .main {{
        height: 100vh;
        width: 100vw;
        margin: 0;
        padding: 0;
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center;
        background-attachment: fixed;
        overflow: hidden;
    }}

    .stApp {{
        background: transparent;
    }}

    [data-testid="stSidebar"], [data-testid="stHeader"] {{
        background: transparent;
    }}

    footer {{
        visibility: hidden;
        height: 0;
    }}

    .stChatMessage {{
        background-color: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
    }}

    div[data-baseweb="input"] > div {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.4);
    }}
    input::placeholder {{
        color: rgba(255,255,255,0.6) !important;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_png_as_page_bg('./assets/background.png')

# --- Page Title ---
st.markdown(
    "<h1 style='text-align: center; color: white;'>RFx AI Builder Assistant</h1>",
    unsafe_allow_html=True
)

# --- Initialize session state ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = initialize_state()

state = st.session_state.conversation_state

# --- Show chat history ---
for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).markdown(msg["content"], unsafe_allow_html=True)

# --- Sidebar for uploads and logs ---
if state["step"] >= 2:
    with st.sidebar:
        st.markdown("## 📄 Document Upload (Optional)")
        uploaded_files = st.file_uploader(
            "Upload supporting RFx Documents",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True
        )
        if uploaded_files:
            filenames_seen = set()
            if "uploaded_texts" not in state:
                state["uploaded_texts"] = []
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in filenames_seen:
                    filenames_seen.add(uploaded_file.name)

                    already_logged = any(
                        f"[Info] User document '{uploaded_file.name}' uploaded" in log
                        for log in state["logs"]
                    )

                    if uploaded_file.name.lower().endswith(".pdf"):
                        try:
                            with pdfplumber.open(uploaded_file) as pdf:
                                content = "\n\n".join(page.extract_text() or "" for page in pdf.pages)
                        except Exception as e:
                            content = ""
                            warning_msg = f"[Warning] Could not extract text from {uploaded_file.name}: {e}"
                            if warning_msg not in state["logs"]:
                                state["logs"].append(warning_msg)
                                st.session_state.highlight_log_index = len(state["logs"]) - 1
                    else:
                        content = uploaded_file.read().decode("utf-8", errors="ignore")

                    state["uploaded_texts"].append({"name": uploaded_file.name, "content": content})

                    if not already_logged:
                        state["logs"].append(f"[Info] User document '{uploaded_file.name}' uploaded")
                        st.session_state.highlight_log_index = len(state["logs"]) - 1

        # 🔁 Removed default logging of "No User document..." here

        st.markdown("## 🧾 RFx Information")
        if state.get("rfx_type"):
            st.markdown(
                f"<div style='background-color:black;padding:0.75rem;border-radius:6px;color:white;font-weight:bold'>Request Type: {state['rfx_type']}</div>",
                unsafe_allow_html=True
            )
        else:
            st.info("No classification yet")

        if state.get("logs"):
            if "highlight_log_index" not in st.session_state:
                st.session_state.highlight_log_index = len(state["logs"]) - 1

            with st.expander("📚 View log steps", expanded=True):
                for idx, log in enumerate(state["logs"]):
                    if idx == st.session_state.highlight_log_index:
                        st.markdown(
                            f"<div style='background-color:black;padding:6px;border-radius:6px;color:#ffffff'>{log}</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(log)

        if st.button("🔁 Reset Chat"):
            st.session_state.chat_history = []
            st.session_state.conversation_state = initialize_state()
            st.rerun()


# --- Step 0: Greet ---
if state["step"] == 0:
    welcome = "Hi! I’m your RFx assistant. How can I help you today?"
    st.chat_message("assistant").write(welcome)
    st.session_state.chat_history.append({"role": "assistant", "content": welcome})
    state["step"] = 1

# --- Step 1: User Input ---
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

# Step 2: trigger classification
if state["step"] == 2 and st.button("Start Building RFx"):
    if not state.get("uploaded_texts"):
        state["logs"].append("[Info] No User document is uploaded")
        st.session_state.highlight_log_index = len(state["logs"]) - 1

    state["logs"].append("[AGENT] Classification agent started")
    st.session_state.highlight_log_index = len(state["logs"]) - 1
    state["trigger_classification"] = True
    st.rerun()

# Step 2: actual classification logic runs on next cycle
if state["step"] == 2 and state.get("trigger_classification"):
    with st.spinner("🔎 Classifying your request..."):
        rfx_type, full_label = run_classification(state)

    if state.get("uploaded_texts"):
        state["logs"].append("[Info] RAG based classification performed: Based on User document")
    else:
        state["logs"].append("[Info] Intent classification performed: Based on User request")

    state["logs"].append(f"[Status] Request type classification complete: {rfx_type}")
    st.session_state.highlight_log_index = len(state["logs"]) - 1

    state["rfx_type"] = rfx_type
    state["step"] = 3
    del state["trigger_classification"]

    msg = f"This looks like a **{rfx_type} ({full_label})**. Do you want to proceed?"
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    st.rerun()

# --- Step 3: Confirm type ---
if state["step"] == 3:
    if state.get("rfx_type") and not state.get("type_confirmed"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, proceed"):
                state["type_confirmed"] = True
                state["logs"].append("[AGENT] Brief Intake agent started. LLM Content generation & Missing details Q&A in progress")
                st.session_state.highlight_log_index = len(state["logs"]) - 1

                with st.spinner("Extracting information from documents...") if state.get("uploaded_texts") else st.empty():
                    brief_data, missing_sections, disclaimer = run_brief(state)

                state["brief_data"] = brief_data
                state["missing_sections"] = missing_sections
                state["disclaimer"] = disclaimer

                confirmed_msg = f"You confirmed the request type: {state['rfx_type']}"
                if not state.get("uploaded_texts"):
                    confirmed_msg += "\n\nSince no supporting documents were uploaded, I'll ask a few questions to help fill in the brief."
                else:
                    confirmed_msg += "\n\nAnalyzing user document contents. I’ll get back if there are any missing details."

                st.chat_message("assistant").write(confirmed_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": confirmed_msg})

                if disclaimer:
                    state["disclaimer_shown"] = True

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

# --- Step 4: Manual selection ---
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

        if missing_sections:
            section, sub = missing_sections[0]
            question = brief_data[section][sub]["question"]
            state["pending_question"] = {"section": section, "sub": sub, "question": question}
            st.chat_message("assistant").write(question)
            st.session_state.chat_history.append({"role": "assistant", "content": question})

        state["step"] = 5
        st.rerun()

# --- Step 5: Q&A if needed ---
if state.get("pending_question"):
    question = state["pending_question"]["question"]
    answer = "N/A"
    if state.get("uploaded_texts", []):
        with st.spinner("LLMs Generating the section content..." + question):
            answer = try_auto_answer(state)

    if answer == "N/A":
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
    else:
        st.chat_message("assistant").write(answer)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        response = process_user_response_to_question(state, answer)
        st.chat_message("assistant").write(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

# --- Step 5: Final document generation ---
if state["step"] == 5 and not state.get("document_generated") and not state.get("pending_question"):
    if st.button("📄 Generate Final RFx Brief"):
        from orchestrator.orchestrator import generate_final_document
        state["logs"].append("[[AGENT] Draft generator agent started")
        st.session_state.highlight_log_index = len(state["logs"]) - 1
        with st.spinner("Generating Word document..."):
            file_path = generate_final_document(state)
            state["document_generated"] = True
            state["document_path"] = file_path
            state["logs"].append("[Status] Final brief available for download")
            st.session_state.highlight_log_index = len(state["logs"]) - 1
            msg = "The final document has been generated. You can download it below."
            st.chat_message("assistant").write(msg)
            st.session_state.chat_history.append({"role": "assistant", "content": msg})
            st.rerun()

if state["step"] == 5 and state.get("document_generated") and state.get("document_path"):
    st.success("Document brief generated!")
    with open(state["document_path"], "rb") as f:
        st.download_button(
            label="⬇️ Download RFx brief",
            data=f,
            file_name="Generated_RFx_document.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )